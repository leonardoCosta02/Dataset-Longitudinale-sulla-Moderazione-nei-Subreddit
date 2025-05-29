from pymongo import MongoClient
from parser.root_parser import root_parser
from scraper.logger_setup import setup_logger
from db.database import wait_for_mongodb
from parser.train_rule_classifier import start_class
import time
import os
logger = setup_logger("parser_logger", to_file=True, log_dir="parser/logger")

def save_to_mongo(doc_id, data, collection, key):
    collection.update_one(
        {"_id": doc_id},
        {"$set": {key: data}},
        upsert=True
    )
#Interroga solo i documenti con "da_parsare": True.+ Passa ogni documento al root_parser. + Salva in regole o moderatori a seconda del contenuto.
#Alla fine di ogni parsing, mette "da_parsare": False.
#Ripete tutto ogni X minuti (default: 2).
def parsing_loop(interval_minutes=2):
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    client = wait_for_mongodb(mongo_uri)
    db = client["reddit_db"]
    collection = db["cache"]
    collection_rules = db["regole"]
    collection_mod = db["moderatori"]

    start_class()  # Carica classificatore e vettorizzatore

    while True:
        docs = list(collection.find({"da_parsare": True}))
        logger.info(f"📥 Trovati {len(docs)} documenti da parsare")

        for doc in docs:
            result = root_parser(doc)
            if result:
                if isinstance(result, list) and result and isinstance(result[0], dict):
                    if 'username' in result[0]:
                        save_to_mongo(doc['_id'], result, collection_mod, "moderatori")
                        logger.info(f"✅ Moderatori salvati per {doc['_id']}")
                    elif 'title' in result[0]:
                        save_to_mongo(doc['_id'], result, collection_rules, "regole")
                        logger.info(f"✅ Regole (wiki) salvate per {doc['_id']}")
                elif isinstance(result, list) and result and isinstance(result[0], str):
                    rules = [{'title': r} for r in result]
                    save_to_mongo(doc['_id'], rules, collection_rules, "regole")
                    logger.info(f"✅ Regole (homepage) salvate per {doc['_id']}")

            # Dopo parsing completato, disattiva il flag anche se non trova layout nel parsing o nessuna regola trovata 
            collection.update_one({"_id": doc["_id"]}, {"$set": {"da_parsare": False}})
                

        logger.info(f"⏳ Attendo {interval_minutes} minuti prima del prossimo ciclo.")
        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    parsing_loop()