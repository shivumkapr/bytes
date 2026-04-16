from data_ingestion.news import data_ingestion

def main():
    print("STARTING DATA INGESTION\n" + "=" * 100 + "\n")
    data_ingestion()
    print("=" * 100 + "\nDONE DATA INGESTION")

if __name__ == "__main__":
    main()