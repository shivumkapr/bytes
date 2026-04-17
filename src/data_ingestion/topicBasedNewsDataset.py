import requests
import time
import json
import os
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import concurrent.futures

load_dotenv()

BASE_URL = "https://gnews.io/api/v4/search"
API_KEY = os.environ.get("GNEWS_API_KEY")

# save a list of articles to a json file
def save_json(data: list) -> None:
    with open("./testing/gnews_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# concurrently scrapes a list of articles and returns the formatted data
def scrape_articles_concurrently(articles_to_scrape: list, topic: str, session: requests.Session) -> list:
    scraped_results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_article = {
            executor.submit(extract_fields, article, session): article 
            for article in articles_to_scrape
        }
        
        for future in concurrent.futures.as_completed(future_to_article):
            try:
                title, description, link, source_name, valid = future.result()
                
                if valid:
                    scraped_results.append({
                        "s": source_name,
                        "t": topic, 
                        "h": title,
                        "d": description 
                    })
            except Exception as exc:
                print(f"    [!] A thread crashed during scraping: {exc}")
                
    return scraped_results

# visits the article URL and extracts paragraph text
def scrape_article_text(url: str, session: requests.Session) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all('p')
        article_text = " ".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        return article_text
    except Exception as e:
        print(f"    [!] Scraping failed for {url}: {e}")
        return ""

# fetches articles from the GNews API for a given topic
def get_gnews_articles(topic: str, time_window: str, session: requests.Session) -> tuple[list, bool]:
    params = {
        "q": topic,           
        "lang": "en",         
        "max": 10,            
        "sortby": "relevance",
        "from": time_window,    
        "apikey": API_KEY
    }
    try:
        response = session.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status() 
        data = response.json()
        return data.get("articles", []), False
    except requests.exceptions.RequestException as e:
        print(f"Network error on topic '{topic}': {e}")
        return [], True

# extracts the needed fields and handles the scraping/fallback logic
def extract_fields(article: dict, session: requests.Session) -> tuple[str, str, str, str, bool]:
    url = article.get("url")
    title = article.get("title", "")
    source_name = article.get("source", {}).get("name", "Unknown Source")

    if not url:
         return "", "", "", "", False

    print(f"  -> Scraping: {title}")
    full_content = scrape_article_text(url, session)
    
    # Fallback: If scraping failed or returned very little text, use GNews description
    if not full_content or len(full_content) < 100:
        print("    [!] Falling back to GNews summary.")
        full_content = article.get("description", "")
        
    return title, full_content, url, source_name, True

def handle_topics(topics: list):
    session = requests.Session()
    
    seen_urls = set()
    seen_titles = set()
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')

    news_data = []

    for topic in topics:
        print(f"\nFetching news for topic: {topic}")
        
        articles, error = get_gnews_articles(topic, yesterday, session)

        if error:
            continue

        articles_to_scrape = []
            
        for article in articles:
            quick_url = article.get("url")
            quick_title = article.get("title", "")
            
            if not quick_url or quick_url in seen_urls or quick_title in seen_titles:
                continue
                
            seen_urls.add(quick_url)
            if quick_title:
                seen_titles.add(quick_title)

            articles_to_scrape.append(article)

        if articles_to_scrape:
            results = scrape_articles_concurrently(articles_to_scrape, topic, session)

            news_data.extend(results)
                        
        time.sleep(1.5) 

    save_json(news_data)
    print(f"\nSuccessfully processed {len(news_data)} unique articles.")