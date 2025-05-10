from pymongo import MongoClient
from app.parser.root_parser import root_parser
from app.scraper.logger_setup import setup_logger

logger = setup_logger("parser_logger", to_file=True, log_dir="app/parser/logger")

if __name__ == "__main__":
    try:
        client = MongoClient("mongodb://localhost:27017/")
        client.admin.command("ping")
        logger.info("✅ MongoDB è attivo e raggiungibile.")
    except Exception as e:
        print("MongoDB non pronto...")

    db = client["reddit_db"]
    collection = db["cache"]

    subreddits = [
        "funny", "de", "FIFA", "fantasyfootball", "hockey",
        "darksouls3", "gaming", "france", "pokemon", "Overwatch"
    ]

    for subreddit in subreddits:
        logger.info(f"🔍 Inizio parsing per subreddit: {subreddit}")

        patterns = [
            rf"https?://(www\.)?reddit\.com/r/{subreddit}/about/moderators/?$",
            rf"https?://(www\.)?reddit\.com/r/{subreddit}/wiki/index/?$",
            rf"https?://(www\.)?reddit\.com/r/{subreddit}/?$",
        ]

        query = {"$or": [{"subreddit": {"$regex": pattern}} for pattern in patterns]}
        #In questo modo prendi tutti i documenti per quel subreddit, sia homepage, sia wiki, sia moderators.
        docs = list(collection.find(query))

        logger.info(f"✅ Trovati {len(docs)} documenti per {subreddit}")

        for doc in docs:
            root_parser(doc)
