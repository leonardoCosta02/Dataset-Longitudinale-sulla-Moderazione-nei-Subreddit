import hashlib
import json
import time
from wayback_client import get_wayback
def insert_html_document(url, file_path, collection):
    """Inserisce nel database un documento con URL e percorso del file HTML.
    
    Questa funzione crea un documento che contiene l'URL e il percorso del file HTML 
    e lo inserisce nella collection di MongoDB passata come parametro. 
    In seguito, stampa una conferma del salvataggio.
    
    Parametri:
    - url (str): L'URL della pagina HTML che è stata scaricata.
    - file_path (str): Il percorso nel file system dove il file HTML è stato salvato.
    - collection (pymongo.collection.Collection): La collection di MongoDB dove il documento sarà inserito.
    
    Ritorna:
    - None
    """
    
    # Crea un dizionario che rappresenta il documento da inserire nel database
    document = {
        "html_url": url,  # Memorizza l'URL nel campo "html_url"
        "file_path": file_path  # Memorizza il percorso del file nel campo "file_path"
    }
    
    # Inserisce il documento creato nella collection di MongoDB
    collection.insert_one(document)
    
    # Stampa un messaggio di conferma che l'inserimento è avvenuto con successo
    print(f"Salvato in MongoDB: {url} -> {file_path}")

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
        # Controlla se la cache è scaduta (ad esempio, cache valida per 24 ore)
        cache_timestamp = cached_doc.get('timestamp')
        if time.time() - cache_timestamp < 86400:  # 86400 secondi = 24 ore
            print(f"Cache hit per {url}")
            return cached_doc["response"]
        else:
            print(f"Cache scaduta per {url}")
            cache_collection.delete_one({"_id": cached_doc["_id"]})  # Rimuovi la cache scaduta
    
    return None

# Funzione per salvare nella cache
#Memorizza la risposta nella collezione cache di MongoDB con un timestamp.
def save_to_cache_db(url, params, response,cache_collection):
    cache_key = get_cache_key(url, params)
    cache_data = {
        "cache_key": cache_key,
        "url": url,
        "params": params,
        "response": response,
        "timestamp": time.time()#La chiamata time.time() restituisce l'ora corrente in secondi dal Epoch (cioè il 1 gennaio 1970, 00:00:00 UTC). Il valore restituito è un numero in virgola mobile che rappresenta il tempo trascorso in secondi, comprensivo di frazioni di secondo.
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
        print("SNapshot già presente in cache")
        return None,7 #con 7 indico che lo snapshot è già stato caricato in precedenza
    else:
    # Se non c'è nella cache, fai la richiesta
        response,err = get_wayback(url, params)
        if response:
            save_to_cache_db(url, params, response.text,cache_collection)  # Salva la risposta nella cache
            return response,err
        return None,err


def log_failed_request(collection_fail, url, error_code):
    collection_fail.insert_one({
        "url": url,
        "error_code": error_code,
        "timestamp": time.time()
    })

def resque_page(base_url,collection_fail):
    # Trova documenti con error_code 2 o 6 e URL Wayback che termina con il base_url
    query = {
        "error_code": {"$in": [2, 6]},
        "url": {"$regex": f"{base_url}$"}  # matcha URL che terminano con quello di interesse
    }

    # Estrai solo il campo 'url'
    #Questa parte:

    #esegue la query su MongoDB (query l’abbiamo definita prima per error_code in [2,6] e url che finisce con l’URL base),

    #chiede di restituire solo il campo url ("url": 1)

    #e di escludere il campo _id ("_id": 0), che MongoDB include di default.

    #è una list comprehension: itera su tutti i risultati della find() e costruisce una lista con solo il valore del campo "url" di ciascun documento
    retry_urls = [doc["url"] for doc in collection_fail.find(query, {"url": 1, "_id": 0})]

    # Verifica
    print(f"Trovati {len(retry_urls)} URL da ritentare:")
    for url in retry_urls:
        print(url)
    return retry_urls
 