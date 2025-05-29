import hashlib
import json
import time
from scraper.wayback_client import get_wayback
from scraper.utils import extract_month
from scraper.utils import get_semester
from scraper.logger_setup import setup_logger
logger = setup_logger(__name__, to_file=True)
# Funzione per generare una chiave di cache univoca
#Questa funzione crea una chiave unica per ogni combinazione di URL e parametri, usando l'hash MD5. 
# Questo assicura che due richieste identiche, anche con parametri complessi, abbiano la stessa chiave di cache.
def get_cache_key(url, params):
    params_str = json.dumps(params, sort_keys=True)  # Serializza i parametri
    return hashlib.md5((url + params_str).encode()).hexdigest()

# Funzione per recuperare dalla cache
#Controlla se esiste una risposta memorizzata per l'URL e i parametri dati. Se la cache è scaduta (in questo caso dopo 24 ore), 
# la rimuove dal database. Puoi regolare la durata della cache come preferisci.
def get_cache_from_db(url, params,cache_collection):
    cache_key = get_cache_key(url, params)
    cached_doc = cache_collection.find_one({"cache_key": cache_key})
    
    if cached_doc:
        
            logger.info(f"Cache hit per {url}")
            return cache_key
        
    return None

# Funzione per salvare nella cache
#Memorizza la risposta nella collezione cache di MongoDB con un timestamp.
def save_to_cache_db(params, response,cache_collection,file_path):
    cache_key = get_cache_key(response.url, params)
    cache_data = {
        "_id": response.url,  # Usa l'URL come ID univoco del documento
        "file_path": file_path , # Memorizza il percorso del file nel campo "file_path"
        "subreddit":  response.url.split("/web/", 1)[1].split("/", 1)[1] , # Estrae l'URL archiviato response.url.split("/web/", 1)[1] → prende tutto dopo /web/.split("/", 1)[1] → rimuove il timestamp lasciando l’URL originale (http://www.reddit.com/r/...)
        "snapshot_year" : int(response.url.split("/")[4][0:4]),
        "semester": f" S{get_semester( extract_month(response.url))}",
        "cache_key": cache_key,
        "timestamp": time.time(),#La chiamata time.time() restituisce l'ora corrente in secondi dal Epoch (cioè il 1 gennaio 1970, 00:00:00 UTC). Il valore restituito è un numero in virgola mobile che rappresenta il tempo trascorso in secondi, comprensivo di frazioni di secondo.
        "da_parsare": True
    }
    cache_collection.replace_one({"cache_key": cache_key}, cache_data, upsert=True)

# Funzione per ottenere la risposta con caching
#Combina la logica di caching con la richiesta HTTP. Se una risposta è presente nella cache, viene restituita; 
# altrimenti, viene eseguita una richiesta e la risposta viene memorizzata nella cache.
#Ora, quando esegui il download delle pagine, la funzione download_single_snapshot_page prima cercherà di recuperare il contenuto dalla cache. Se non è disponibile, scaricherà la pagina e la salverà, memorizzandola nella cache per usi futuri.
#Questo approccio riduce il carico di richieste HTTP verso Wayback Machine e ottimizza il processo, recuperando rapidamente le pagine già scaricate.
def get_wayback_with_cache_mongo(url, params,cache_collection):
    cached_response = get_cache_from_db(url, params,cache_collection)
    if cached_response:
        logger.info("SNapshot già presente in cache")
        return None,7 #con 7 indico che lo snapshot è già stato caricato in precedenza
    else:
    # Se non c'è nella cache, fai la richiesta
        response,err = get_wayback(url, params)
        if response:
           
            return response,err
        return None,err


def log_failed_request(collection_fail, url, error_code):
    fatal = error_code in (3, 4, 5)

    error_entry = {
        "error_code": error_code,
        "timestamp": time.time(),
        
    }
    

    #Se è la prima volta, crea il documento con _id = url e la lista errors con un solo elemento.
    #Se esiste già, aggiunge il nuovo errore alla lista errors. crea il documento se non esiste, aggiorna fatal, e aggiunge l’errore alla lista errors.

    collection_fail.update_one(
        {"_id": url},
        {
            "$set": {"fatal": fatal},
            "$push": {"errors": error_entry}
        },
        upsert=True
    )

def remove_document(collection_fail, doc):
    """Rimuove il documento con il dato _id dalla collection."""
    collection_fail.delete_one({"_id": doc})
    logger.info(f"[remove_document] Documento con _id {doc} eliminato dal database.")

def resque_page(urls, collection_fail):
    cursor = collection_fail.find({
        "_id": {"$in": urls},
        "fatal": False
    })
    #Se il  cursor restituisce 2 documenti come questi:
    #{ "_id": "https://reddit.com/r/AskReddit", "fatal": false }
    #{ "_id": "https://reddit.com/r/Python", "fatal": false }
    #Allora recoverable_urls sarà:
    #[
    #"https://reddit.com/r/AskReddit",
    #"https://reddit.com/r/Python"]


    recoverable_urls = [doc["_id"] for doc in cursor]

    if recoverable_urls:
        logger.info("[resque_page] URL da recuperare:")
        for url in recoverable_urls:
            logger.info(f"  - {url}")
    else:
        logger.info("[resque_page] Nessun URL da recuperare.")

    return recoverable_urls


import time
from pymongo import MongoClient
def wait_for_mongodb(uri, interval=15):
    """Aspetta che MongoDB sia disponibile, fino a timeout secondi."""
    
    while True:
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            client.admin.command("ping")
            logger.info("✅ MongoDB è attivo e raggiungibile.")
            return client
        except Exception as e:
           
            logger.info("⏳ In attesa che MongoDB sia pronto...")
            time.sleep(interval)

