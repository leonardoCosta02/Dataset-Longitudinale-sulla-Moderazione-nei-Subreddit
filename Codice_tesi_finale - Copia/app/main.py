import os  # Importa il modulo os per interagire con il filesystem (per creare cartelle, gestire file, ecc.)
from pymongo import MongoClient,errors  # Importa il client di MongoDB per interagire con il database
import time  # Modulo per gestire le operazioni temporali (es. sleep)
import random  # Modulo per generare numeri casuali
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scraper.scraper import get_snapshot_urls  # Funzione per recuperare gli snapshot da Wayback Machine
from scraper.utils import get_valid_snapshot  # Funzione per filtrare gli snapshot validi
from scraper.scraper import download_single_snapshot_page
from scraper.logger_setup import setup_logger
from db.database import resque_page,wait_for_mongodb
from db.database import remove_document
from scraper.utils import leggi_subreddit_da_tsv
SNAPSHOTS_PER_YEAR = int(os.environ["SNAPSHOTS_PER_YEAR"])

logger = setup_logger(__name__, to_file=True)
def scrape_snapshots(url):
    
    error_urls = []  # Qui raccogli gli URL falliti
    all_snapshots = get_snapshot_urls(url)
    
    if not all_snapshots:
        logger.warning(f"Nessun snapshot trovato per {url}")
        return

    for year in range(2012, 2024):
        # Filtra gli snapshot dell'anno corrente
        year_snapshots = [snap for snap in all_snapshots if f"/{year}" in snap]

          

        if not year_snapshots:
            logger.info(f"{year}: Nessun snapshot per l'anno {year}")
            continue

        downloaded_count = 0 # Contatore degli snapshot validi scaricati per questo anno

        while downloaded_count < SNAPSHOTS_PER_YEAR:
            first = get_valid_snapshot(year_snapshots, 1, 12)
            if not first:
                logger.warning(f"⚠️ Nessun altro snapshot valido disponibile per l'anno {year}")
                break

            success = download_single_snapshot_page(first[0], cache_collection, collection_fail, error_urls)

            # Continua finché non scarica SNAPSHOTS_PER_YEAR snapshot validi o finché non ha esaurito i candidati
            #entro qui se ho preso una pagina con errori non recuperabili o redirect fuori semestre o fuori anno 
            # Se snapshot non valido, rimuovo first[0] dalla lista snapshot dell'anno
            while not success and year_snapshots and first:
                if first[0] in year_snapshots:
                    year_snapshots.remove(first[0])
                    logger.warning(f"🗑️  Rimosso snapshot non valido: {first[0]}")
                    logger.warning("Provo a prendere il prossimo snapshot")
                    first = get_valid_snapshot(year_snapshots, 1, 12)
                    if first:
                        success = download_single_snapshot_page(first[0], cache_collection, collection_fail, error_urls)

            if success:
                # snapshot valido scaricato, incremento contatore
                if first[0] in year_snapshots:
                    year_snapshots.remove(first[0])
                downloaded_count += 1
                time.sleep(random.uniform(1, 3))


        

    
    logger.info(f" url che mi hanno causato errori{error_urls} ")
    logger.info("Adesso provo a recuperare le pagine web che possono essere recuperate se ci sono ")
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
    """
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
    
    """
    url_templates = [
        "https://www.reddit.com/r/{}/about/moderators",
        "https://old.reddit.com/r/{}/about/moderators",
        "https://www.reddit.com/r/{}/wiki/index",
        "https://old.reddit.com/r/{}",
        "https://www.reddit.com/r/{}"



    ]
    
    
    
    try:
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        client = wait_for_mongodb(mongo_uri)  # Usa la funzione per aspettare MongoDB
        db = client["reddit_db"]
        cache_collection = db["cache"]
        collection_fail = db["fail"]

        CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "html_cache")
        logger.info(f"stampo cache dir {CACHE_DIR}")
        os.makedirs(CACHE_DIR, exist_ok=True)

        subreddits = leggi_subreddit_da_tsv("/embedding-metadata.tsv")  # Percorso assoluto nel container
        for subreddit in subreddits:
            for template in url_templates:
                url = template.format(subreddit)
                logger.info(f"🔍 Inizio scraping per {url}")
                scrape_snapshots(url)

    except errors.ServerSelectionTimeoutError as e:
        logger.warning("❌ Errore: impossibile connettersi a MongoDB.")
        logger.warning(f"Dettagli: {e}")
    except Exception as e:
        logger.warning("❌ Errore generico durante la connessione a MongoDB.")
        logger.warning(f"Dettagli: {e}")