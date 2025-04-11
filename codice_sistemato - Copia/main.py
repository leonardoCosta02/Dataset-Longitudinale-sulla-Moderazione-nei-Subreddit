import os  # Importa il modulo os per interagire con il filesystem (per creare cartelle, gestire file, ecc.)
from pymongo import MongoClient  # Importa il client di MongoDB per interagire con il database
import time  # Modulo per gestire le operazioni temporali (es. sleep)
import random  # Modulo per generare numeri casuali
from scraper import get_snapshot_urls  # Funzione per recuperare gli snapshot da Wayback Machine
from utils import get_valid_snapshot  # Funzione per filtrare gli snapshot validi
from scraper import download_single_snapshot_page
from logger_setup import setup_logger
from database import resque_page
from utils import extract_month
from database import log_failed_request
logger = setup_logger(__name__, to_file=True)
def scrape_snapshots(url):
    

    all_snapshots = get_snapshot_urls(url)
    if not all_snapshots:
        logger.warning(f"Nessun snapshot trovato per {url}")
        return

    for year in range(2012, 2025):
        # Filtra gli snapshot dell'anno corrente
        year_snapshots = [snap for snap in all_snapshots if f"/{year}" in snap]

          

        if not year_snapshots:
            print(f"{year}: Nessun snapshot per l'anno {year}")
            continue

        # Cerca i due snapshot validi
        first = get_valid_snapshot(year_snapshots, 1, 6)
        second = get_valid_snapshot(year_snapshots, 7, 12)
        #check se gli snapshot scelti abbiano una distanza temporale di almeno 4 mesi in python non esiste direttamente il do while
        ok=True
        tentativo=8
        if first is not None and second is not None :
            while ok and tentativo<=12:
                if second is None:
                    break  # Uscita sicura dal ciclo se non ci sono più snapshot validi
                
                if(extract_month(second[0])-extract_month(first[0])<4):
                    tentativo += 1
                    second = get_valid_snapshot(year_snapshots, tentativo, 12)
                else:
                    ok=False
        
        if first:
            success = download_single_snapshot_page(first[0], collection,cache_collection,collection_fail)
            if success:
                time.sleep(random.uniform(1, 3))
        else:
            logger.warning(f"⚠️ Nessun snapshot valido per il primo semestre {year}")

        if second:
            success = download_single_snapshot_page(second[0], collection,cache_collection,collection_fail)
            if success:
                time.sleep(random.uniform(1, 3))
        else:
            logger.warning(f"⚠️ Nessun snapshot valido per il secondo semestre {year}")
    
    print("Adesso provo a recuperare le pagine web che possono essere recuperate se ci sono ")
    resque=resque_page(url,collection_fail)
   
    if resque is not None:
        time.sleep(30)
        for doc in resque:
            success = download_single_snapshot_page(doc, collection,cache_collection,collection_fail)
            if success:
                log_failed_request(collection_fail, doc, 8) # 8 implica che la pagina è stata recuperata e la metto nel db 
                time.sleep(random.uniform(1, 3))


if __name__ == "__main__":
    # Connessione al database MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["reddit_db"]  # Seleziona il database
    collection = db["subreddit_html"]  # Seleziona la collezione per salvare i dati
    cache_collection = db["cache"]
    collection_fail=db["fail"]
    CACHE_DIR = "html_cache"  # Cartella per il salvataggio delle pagine HTML
    os.makedirs(CACHE_DIR, exist_ok=True)  # Crea la cartella se non esiste
    
    # Richiesta degli URL da analizzare
    urls = input("Inserisci  URL da analizzare  ")
    
    # Esecuzione dello scraping in parallelo utilizzando ThreadPoolExecutor
    scrape_snapshots(urls)   
