from data_ingestion.dailyNewsDataset import data_ingestion
from data_ingestion.topicBasedNewsDataset import handle_topics

def main():
    print("STARTING DATA INGESTION\n" + "=" * 100 + "\n")
    data_ingestion()
    print("=" * 100 + "\nDONE DATA INGESTION")

    # TODO: placeholder to make LLM call to extract topics
    MOCK_TOPICS = ["Iran peace", "Stock market", "FIFA World Cup"]
    handle_topics(MOCK_TOPICS)

if __name__ == "__main__":
    main()