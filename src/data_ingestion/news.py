import feedparser
import requests
from requests import Session
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from time import mktime

NEWS_FEEDS = {
    "General": {
        "New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "BBC Top Stories": "https://feeds.bbci.co.uk/news/rss.xml",
        "NPR Top Stories": "https://feeds.npr.org/1001/rss.xml",
        "NPR World": "https://feeds.npr.org/1004/rss.xml",
        "ABC News": "https://abcnews.go.com/abcnews/topstories",
        "The Guardian (World)": "https://www.theguardian.com/world/rss",
        "The Guardian (US)": "https://www.theguardian.com/us-news/rss",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "CBS News": "https://www.cbsnews.com/latest/rss/main",
    },
    "Politics": {
        "WSJ World News": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
        "WSJ Politics": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
        "The Hill": "https://thehill.com/homenews/feed/",
        "Axios Politics": "https://www.axios.com/feeds/feed.rss",
        "NPR Politics": "https://feeds.npr.org/1014/rss.xml",
        "BBC Politics": "https://feeds.bbci.co.uk/news/politics/rss.xml",
    },
    "Business": {
         "WSJ Markets": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
        "BBC Business": "https://feeds.bbci.co.uk/news/business/rss.xml",
        "NPR Business": "https://feeds.npr.org/1006/rss.xml",
    },
    "Technology": {
        "BBC Technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
        "The Verge": "https://www.theverge.com/rss/index.xml",
        "TechCrunch": "https://techcrunch.com/feed/",
        "NPR Science": "https://feeds.npr.org/1007/rss.xml",
    },
    "Sports": {
        "BBC Sport": "https://feeds.bbci.co.uk/sport/rss.xml",
        "ESPN": "https://www.espn.com/espn/rss/news"
    }
}

TEST_NEWS_FEED = {
    "General": {
        "New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    }
}

# return the RSS feed of one source along with error flag for malformed data
def get_feed(url: str, session: Session) -> tuple[list, bool]:
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        
        if not feed.get("entries"):
            return [], True
            
        return feed["entries"], False
        
    except requests.RequestException as e:
        return [], True

# return the title and clean description of one valid (within 24 hours) entry
def extract_fields(entry: dict, time_window: datetime) -> tuple[str, str, str, bool]:

    published_time = entry.get("published_parsed", None)

    if not published_time:
        return "", "", "", False   
    
    pub_time = datetime.fromtimestamp(mktime(published_time), timezone.utc)
    
    if pub_time < time_window:
        return "", "", "", False   


    title = entry.get("title", "")
    description = entry.get("summary", "")
    cleaned_description = BeautifulSoup(description, "html.parser").get_text(separator=" ").strip()
    link = entry.get("link", "")
    
    return title, cleaned_description, link, True

# save a list of articles to a json file
def save_json(data: list) -> None:
    with open("./testing/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def data_ingestion():
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) NewsValidator/1.0'})

    time_window = datetime.now(timezone.utc) - timedelta(days=1)

    """
        list to store news data andsave to json

        [
            {
                s: "sources such as CNN or BBC"
                f: "feeds such as Technology or Business"
                t: "titles of the article"
                d: "short description of the article"
            }
        ]

    """
    news_data = []
    seen_urls = set()

    for feed, sources in NEWS_FEEDS.items():
        for channel, url in sources.items():
            print(f"Pulling articles from {channel}'s RSS feed")
            print("#" * 50 + "\n")

            entries, error = get_feed(url, session)

            if error:
                continue

            for entry in entries:
                title, description, link, valid = extract_fields(entry, time_window)

                if not valid:
                    continue

                # de-dupe seen urls  
                if link in seen_urls:
                    continue
                seen_urls.add(link)

                news_data.append(
                    {
                        "s": channel,
                        "f": feed,
                        "t": title,
                        "d": description,
                    }
                )
    save_json(news_data)