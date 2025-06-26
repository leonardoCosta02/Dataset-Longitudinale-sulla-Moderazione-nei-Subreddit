from pymongo import MongoClient
from parser.root_parser import root_parser
from scraper.logger_setup import setup_logger
from db.database import wait_for_mongodb
from parser.train_rule_classifier import start_class
import time
import os
logger = setup_logger("parser_logger", to_file=True, log_dir="parser/logger")

#Se esiste già un documento con _id == doc_id, allora MongoDB non lo inserisce nuovamente, ma aggiorna il campo key con il valore data.
#Se non esiste, allora MongoDB inserisce un nuovo documento con _id == doc_id e il campo key impostato a data.
#upsert=False (default): Se il documento non esiste, non fa nulla.  Se il documento esiste, lo aggiorna.
#upsert=True: Se il documento esiste, lo aggiorna. Se il documento non esiste, lo inserisce come nuovo documento, usando il filtro ({"_id": doc_id} nel tuo caso) come base.
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
                #✅ Se il risultato è:
                #una lista non vuota e il primo elemento è un dizionario (dict)
                #Allora può essere o una lista di moderatori o una lista di regole da wiki
                
                if isinstance(result, list) and result and isinstance(result[0], dict):

                    #Se il primo elemento contiene la chiave "username", allora è sicuramente una lista di moderatori.
                    if 'username' in result[0]:
                        save_to_mongo(doc['_id'], result, collection_mod, "moderatori")
                        logger.info(f"✅ Moderatori salvati per {doc['_id']}")

                    # # ⚠️ Qui finisce sia wiki che old_homepage
                    elif 'title' in result[0]:
                        save_to_mongo(doc['_id'], result, collection_rules, "regole")
                        logger.info(f"✅ Regole (wiki) salvate per {doc['_id']}")

                #Se il parser ha restituito: una lista non vuota di sole stringhe CASO HOMEPAGE ( nuova)
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


"""
CASO 1 — Moderatori (about/moderators o old/.../about/moderators)

Output result: una lista di dizionari (uno per ogni moderatore)

result = [
    {
        "username": "moderator1",
        "permissions": ["all"],
        "mod_since": "2020-01-01"
    },
    {
        "username": "moderator2",
        "permissions": ["posts", "wiki"],
        "mod_since": "2021-05-12"
    },
    ...
]

Uso di result[0]:

result[0] = {
    "username": "moderator1",
    ...
}

----------------------------------------
CASO 2 — Regole dalla Wiki (/wiki/index)
Output result: lista di dizionari (una per regola)

result = [
    {
        "number": 1,
        "title": "Be kind",
        "description": "Treat others with respect."
    },
    {
        "number": 2,
        "title": "No spam",
        "description": "Avoid posting repetitive content."
    },
    ...
]

Uso di result[0]:

result[0] = {
    "number": 1,
    "title": "Be kind",
    ...
}

-----------------------------------------------
CASO 3 — Regole dalla Homepage (nuova)

Output result: lista di stringhe (solo titoli delle regole)

result = [
    "Don't post memes",
    "Use spoiler tags",
    "No self-promotion"
]

Uso di result[0]:

result[0] = "Don't post memes"

 È una str, quindi sappiamo che sono solo titoli, e il codice li trasforma in:

 rules = [{'title': r} for r in result]

------------------------------------------------------------
CASO 4 — Regole da Homepage vecchia (old.reddit.com/r/...)

Output result: lista di dizionari (titolo + descrizione)

result = [
    {
        "number": 1,
        "title": "No clickbait",
        "description": "Post titles must reflect the content."
    },
    {
        "number": 2,
        "title": "Tag NSFW content",
        "description": "Clearly mark adult content."
    },
    ...
]

Uso di result[0]:

result[0] = {
    "number": 1,
    "title": "No clickbait",
    ...
}

→ Anche qui 'title' in result[0] ⇒ sono regole.

"""