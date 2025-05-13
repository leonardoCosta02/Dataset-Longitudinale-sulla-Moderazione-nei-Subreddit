from pymongo import MongoClient
from parser.root_parser import root_parser
from scraper.logger_setup import setup_logger
from db.database import wait_for_mongodb
import os
logger = setup_logger("parser_logger", to_file=True, log_dir="parser/logger")

def save_to_mongo(doc_id, data, collection, key):
    collection.update_one(
        {"_id": doc_id},
        {"$set": {key: data}},
        upsert=True
    )
if __name__ == "__main__":
    try:
        mongo_uri = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")#mongodb://mongodb: il secondo è il nome del servizio che ho creato 
        client = wait_for_mongodb(mongo_uri)  # Usa la funzione per aspettare MongoDB
    except Exception as e:
        print("MongoDB non pronto...")

    db = client["reddit_db"]
    collection = db["cache"]
    collection_rules=db["regole"]
    collection_mod=db["moderatori"]

    subreddits = [
        "funny", "FIFA", "fantasyfootball", "hockey",
        "darksouls3", "gaming","pokemon", "Overwatch","AskReddit",
        "guns","halo"
    ]

    for subreddit in subreddits:
        logger.info(f"🔍 Inizio parsing per subreddit: {subreddit}")

        patterns = [
            rf"https?://(www\.)?reddit\.com/r/{subreddit}/about/moderators/?$",
            rf"https?://(www\.)?reddit\.com/r/{subreddit}/wiki/index/?$",
            rf"https?://(www\.)?reddit\.com/r/{subreddit}/?$",
            rf"https?://(old\.)?reddit\.com/r/{subreddit}/?$",
            rf"https?://(old\.)?reddit\.com/r/{subreddit}/about/moderators/?$"
        ]

        query = {"$or": [{"subreddit": {"$regex": pattern}} for pattern in patterns]}
        #In questo modo prendi tutti i documenti per quel subreddit, sia homepage, sia wiki, sia moderators.
        docs = list(collection.find(query))

        logger.info(f"✅ Trovati {len(docs)} documenti per {subreddit}")

        for doc in docs:
            """
            Chiama il parser principale che restituisce:

            una lista di dizionari (moderatori o regole wiki), oppure

            una lista di stringhe (regole da homepage)
            """
            result = root_parser(doc)
            if result:
                if isinstance(result, list) and result and isinstance(result[0], dict):
                    if 'username' in result[0]:  # È la lista dei moderatori
                        save_to_mongo(doc['_id'], result, collection_mod,"moderatori")
                        logger.info(f"✅ Moderatori salvati per {doc['_id']}")
                    elif 'title' in result[0] or 'description' in result[0]:  # wiki rules
                        save_to_mongo(doc['_id'], result, collection_rules,"regole")
                        logger.info(f"✅ Regole (wiki) salvate per {doc['_id']}")
                elif isinstance(result, list) and result and isinstance(result[0], str):
                    # È una lista di regole come stringhe (homepage)
                    rules = [{'title': r} for r in result]
                    save_to_mongo(doc['_id'], rules, collection_rules,"regole")
                    logger.info(f"✅ Regole (homepage) salvate per {doc['_id']}")


