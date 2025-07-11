from db.database import get_wayback_with_cache_mongo
from scraper.utils import get_semester, save_html_page
from scraper.logger_setup import setup_logger
from scraper.wayback_client import get_wayback
from db.database import log_failed_request
from scraper.wayback_client import get_wayback
from db.database import save_to_cache_db
import time
logger = setup_logger(__name__, to_file=True)
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Pixel 4 XL Build/QP1A.190711.020) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
]


def get_snapshot_urls(url):
    """
    Funzione per ottenere tutti gli snapshot disponibili dal 2012 al 2024.
    
    Parametri:
    - url (str): L'URL della pagina web da cui recuperare gli snapshot.

    Ritorna:
    - List[str]: Una lista di URL degli snapshot.

    risposta in JSON:
    [
    ["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"],
    ["com,reddit)/r/funny", "20130115000000", "http://www.reddit.com/r/funny", "text/html", "200", "ABC123DEF456", "12345"],
    ["com,reddit)/r/funny", "20130701000000", "http://www.reddit.com/r/funny", "text/html", "200", "XYZ789GHI012", "67890"],
    ...
    ]
    entry[1] → timestamp
    entry[2] → original

    Risposta JSON:
        [
            ["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"],
            ["com,reddit)/r/funny", "20120115093200", "http://www.reddit.com/r/funny", "text/html", "200", "ABC123XYZ", "45973"],
            ["com,reddit)/r/funny", "20130610102115", "http://www.reddit.com/r/funny", "text/html", "200", "DEF456UVW", "48201"],
            ["com,reddit)/r/funny", "20141205124500", "http://www.reddit.com/r/funny", "text/html", "200", "GHI789JKL", "50321"],
            ["com,reddit)/r/funny", "20170702080000", "http://www.reddit.com/r/funny", "text/html", "200", "MNO321RST", "51890"],
            ["com,reddit)/r/funny", "20211110101010", "http://www.reddit.com/r/funny", "text/html", "200", "PQR654LMN", "54712"]
        ]

    """
    base_url = f"https://web.archive.org/cdx/search/cdx"
    logger.info(f"🚀 Richiesta snapshot per {url} (2012–2024)")
    params = {
    "url": url,
    "from": "2012",
    "to": "2024",
    "output": "json",
    "collapse": "digest"
    }
    
    #se quando faccio richiesta con  api ho errore 2  provo due volte 
    #perchè prima non vedevo codice errore e restituivo null se c era qualsiasi errore 
    #perciò se era recuperabile la richiesta all'api non la rifacevo 
    #qua invece provo due volte 
    i=0
    while i<2:
     response, err_code = get_wayback(base_url,params)
     if response is None:
        if err_code==2:
            logger.warning(f"Errore di tipo 2  nella richiesta all'api attendo e riprovo un altra volta")
            time.sleep(30)
            i+=1
        else:
            logger.error(f"❌ Nessuna risposta per {url}")
            return []
     else:
         i=2

    try:
        data = response.json()
        logger.info(f"✅ {len(data) - 1} snapshot trovati per {url}")
        return [f"https://web.archive.org/web/{entry[1]}/{entry[2]}" for entry in data[1:]]
    except Exception as e:
        logger.error(f"❌ Errore nel parsing JSON per {url}: {e}")
        return []
    

def download_single_snapshot_page(url,cache_collection,collection_fail,error_list, expected_month=None):
    """
    Scarica una singola pagina snapshot dalla Wayback Machine, con gestione avanzata degli errori.

    Parametri:
    - url (str): L'URL dello snapshot da scaricare.
    - collection (MongoDB Collection): Collezione MongoDB per i metadati.
    - expected_month (int): Mese previsto per verificare i redirect.
    - max_attempts (int): Numero massimo di tentativi.

    Ritorna:
    - bool: True se il download ha avuto successo, False altrimenti.
    """
    expected_month= int(url.split("/")[4][4:6])
    expected_year=int(url.split("/")[4][0:4])  # Es: .../web/202307... => 2023
    logger.info(f"⬇️ Downloading snapshot: {url}")
    response,err_code = get_wayback_with_cache_mongo(url, {},cache_collection)
    if response is None:
        if err_code == 7:
            # Snapshot già in cache, quindi non loggare niente
            return True
        
        log_failed_request(collection_fail, url, err_code)
        logger.error(f"❌ Errore tipo {err_code} per {url}")
        error_list.append(url)
        if err_code ==3 or err_code == 4 or err_code == 5: 
         return False
        else:
            logger.info(f"errore che mi permette di provare di recuperare la pagina dopo ")  
            return True    

    final_url = response.url
    if  final_url != url:
        # Controllo del redirect: estrae la data dallo snapshot
        redirected_month = int(final_url.split("/")[4][4:6])  # Es: .../web/202307... => 07
        redirected_year= int(final_url.split("/")[4][0:4])
        if get_semester(redirected_month) != get_semester(expected_month):
            logger.warning(f"⚠️ Redirect fuori semestre: da {url} a {final_url}")
            return False
        if redirected_year != expected_year:
            logger.warning(f"⚠️ Redirect fuori anno: da {url} a {final_url}")
            return False
        

    file_path = save_html_page(final_url, response.text)
    save_to_cache_db({}, response,cache_collection,file_path)  # Salva la risposta nella cache
    logger.info(f"✅ Pagina scaricata con successo: {final_url}")
    return True



        

