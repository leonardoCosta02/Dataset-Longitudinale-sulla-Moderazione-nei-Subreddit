import os  # Importa il modulo os per interagire con il filesystem (per creare cartelle, gestire file, ecc.)
from pymongo import MongoClient,errors  # Importa il client di MongoDB per interagire con il database
import time  # Modulo per gestire le operazioni temporali (es. sleep)
import random  # Modulo per generare numeri casuali
from scraper import get_snapshot_urls  # Funzione per recuperare gli snapshot da Wayback Machine
from utils import get_valid_snapshot  # Funzione per filtrare gli snapshot validi
from scraper import download_single_snapshot_page
from logger_setup import setup_logger
from database import resque_page
from database import remove_document
from utils import leggi_subreddit_da_tsv
logger = setup_logger(__name__, to_file=True)
def scrape_snapshots(url):
    
    error_urls = []  # Qui raccogli gli URL falliti
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
        
        
        if first:
            success = download_single_snapshot_page(first[0],cache_collection,collection_fail,error_urls)
            if success:
                time.sleep(random.uniform(1, 3))
            else:#entro qui se ho preso una pagina con errori non recuperabili o redirect fuori semestre o fuori anno 
                 # Se snapshot non valido, rimuovo first[0] dalla lista snapshot dell'anno
                
                    
                    while success== False and year_snapshots and first:
                      if first[0] in year_snapshots:
                        year_snapshots.remove(first[0])
                        logger.warning(f"🗑️  Rimosso snapshot non valido: {first[0]}")
                        logger.warning(f"Provo a prendere il prossimo snapshot ")
                        first = get_valid_snapshot(year_snapshots, 1, 6)
                        if first:
                         success = download_single_snapshot_page(first[0],cache_collection,collection_fail,error_urls)  
                       
        else:
            logger.warning(f"⚠️ Nessun snapshot valido per il primo semestre {year}")

        if second:
            success = download_single_snapshot_page(second[0],cache_collection,collection_fail,error_urls)
            if success:
                time.sleep(random.uniform(1, 3))
            else:#entro qui se ho preso una pagina con errori non recuperabili o redirect fuori semestre o fuori anno 
                 # Se snapshot non valido, rimuovo second[0] dalla lista snapshot dell'anno
                
                    while success== False and year_snapshots and second:
                      if second[0] in year_snapshots:
                        year_snapshots.remove(second[0])
                        logger.warning(f"🗑️  Rimosso snapshot non valido: {second[0]}")
                        logger.warning(f"Provo a prendere il prossimo snapshot ")
                        second = get_valid_snapshot(year_snapshots, 7, 12)
                        if second: 
                            success = download_single_snapshot_page(second[0],cache_collection,collection_fail,error_urls)
                    

                           
        else:
            logger.warning(f"⚠️ Nessun snapshot valido per il secondo semestre {year}")
    
    print(f" url che mi hanno causato errori{error_urls} ")
    print("Adesso provo a recuperare le pagine web che possono essere recuperate se ci sono ")
    resque=resque_page(error_urls,collection_fail)
   
    if resque is not None:
        time.sleep(30)
        for doc in resque:
            success = download_single_snapshot_page(doc,cache_collection,collection_fail,error_urls,)
            if success:
                remove_document(collection_fail, doc) 
                time.sleep(random.uniform(1, 3))


if __name__ == "__main__":
    # Template degli URL da generare per ogni subreddit
    url_templates = [
        "https://old.reddit.com/r/{}/about/rules",
        "https://old.reddit.com/r/{}/about/rules/.json",
        "https://www.reddit.com/mod/{}/rules",
        "https://www.reddit.com/r/{}",
        "https://old.reddit.com/r/{}",
        "https://old.reddit.com/r/{}/about/moderators/.json",
        "https://old.reddit.com/r/{}/about/moderators",
        "https://www.reddit.com/mod/{}/moderators",
    ]
    
    
    try:
        # Tentativo di connessione a MongoDB
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)  # Timeout a 3 secondi
        client.admin.command('ping')  # Comando per testare la connessione

        # Connessione riuscita
        print("✅ Connessione a MongoDB riuscita.")

        db = client["reddit_db"]
        cache_collection = db["cache"]
        collection_fail = db["fail"]
        CACHE_DIR = "html_cache"  # Cartella per il salvataggio delle pagine HTML
        os.makedirs(CACHE_DIR, exist_ok=True)  # Crea la cartella se non esiste
         # Lettura e stampa dei subreddit
        subreddits = leggi_subreddit_da_tsv("embedding-metadata.tsv")
        for subreddit in subreddits:
            for template in url_templates:
                url = template.format(subreddit)
                logger.info(f"🔍 Inizio scraping per {url}")
                scrape_snapshots(url)
        

    except errors.ServerSelectionTimeoutError as e:
        print("❌ Errore: impossibile connettersi a MongoDB.")
        print(f"Dettagli: {e}")
    except Exception as e:
        print("❌ Errore generico durante la connessione a MongoDB.")
        print(f"Dettagli: {e}")