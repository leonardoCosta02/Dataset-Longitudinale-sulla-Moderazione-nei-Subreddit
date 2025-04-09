import re 
from logger_setup import setup_logger
logger = setup_logger(__name__, to_file=True)

def sanitize_filename(url):
    # Sostituisci i caratteri non validi (inclusi '?', '=', '&', ':', '/', etc.) con '_'
    return re.sub(r'[\\/*?:"<>|&=]', '_', url)

def extract_month(url):
    """
    Estrae il mese dall'URL di uno snapshot Wayback Machine.
    
    Parametri:
    url (str): L'URL dello snapshot.
    
    Ritorna:
    int | None: Il numero del mese (1-12) se estratto correttamente, altrimenti None.
    """
    try:
        # L'URL degli snapshot contiene la data nel formato AAAAMMGG (es. 20230415 per il 15 aprile 2023)
        return int(url.split("/")[4][4:6])  # Prende i caratteri 4-6 della data per ottenere il mese
    except (IndexError, ValueError):
        # Se la struttura dell'URL non è corretta o non può essere convertita in intero, ritorna None
        return None


def get_valid_snapshot(urls, start_month, end_month):
    """
    Trova il primo snapshot disponibile in un determinato intervallo di mesi.
    
    Parametri:
    urls (list): Lista di URL degli snapshot.
    start_month (int): Mese di inizio dell'intervallo (1-12).
    end_month (int): Mese di fine dell'intervallo (1-12).
    
    Ritorna:
    tuple | None: Una tupla contenente l'URL valido e il suo mese, oppure None se nessun snapshot è valido.
    """
    for url in urls:
        month = extract_month(url)  # Estrae il mese dall'URL
        if month and start_month <= month <= end_month:  # Controlla se è nell'intervallo desiderato
            return url, month  # Ritorna il primo URL valido con il suo mese
    
    return None  # Nessuno snapshot valido trovato


def get_semester(month):
    return 1 if 1 <= month <= 6 else 2


import os
from urllib.parse import urlparse
from utils import sanitize_filename  # Assicurati che questa funzione sia disponibile
import logging

logger = logging.getLogger(__name__)

#Riceve un URL come https://web.archive.org/web/20230701000000/https://www.reddit.com/r/Python/
#Estrae dalla parte finale del path il nome del subreddit (python), cercando la sottostringa /r/<subreddit>/
#Restituisce "python" (in lowercase), oppure "unknown" se non riesce.
#🎯 Serve per capire a quale subreddit appartiene quella pagina HTML.
def extract_subreddit_from_url(url):
    """
    Estrae il nome del subreddit da un URL Reddit (es. '/r/python/' => 'python').

    Parametri:
    - url (str): L'URL completo dello snapshot

    Ritorna:
    - subreddit (str): Il nome del subreddit in lowercase, o 'unknown' se non trovato
    """
    try:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.lower().split('/')
        if 'r' in path_parts:
            r_index = path_parts.index('r')
            if r_index + 1 < len(path_parts):
                return path_parts[r_index + 1]
    except Exception as e:
        logger.warning(f"❗ Impossibile estrarre subreddit da URL: {url} - Errore: {e}")
    return "unknown"

#Prende l’URL completo dello snapshot
#Chiama extract_subreddit_from_url() per ottenere il nome del subreddit
#Prende le prime 3 lettere del subreddit per costruire una sottocartella (es. pyt)
#Usa sanitize_filename() per trasformare l’URL in un nome file valido (senza caratteri strani)
#Costruisce il path finale completo:
#html_cache/pyt/<nome_file_sanitizzato>.html
#Se la directory html_cache/pyt/ non esiste, la crea.
#📁 Esempio di output:
#html_cache/pyt/web.archive.org_web_20230701000000_https_www.reddit.com_r_python.html
def get_html_file_path(url):
    """
    Costruisce il percorso del file HTML usando una sottocartella basata sul nome del subreddit.

    Parametri:
    - url (str): L'URL della pagina da salvare

    Ritorna:
    - file_path (str): Il percorso completo del file dove salvare l'HTML
    """
    subreddit = extract_subreddit_from_url(url)
    prefix = subreddit[:3] if subreddit else "unk"

    # Crea la directory se non esiste
    dir_path = os.path.join("html_cache", prefix)
    os.makedirs(dir_path, exist_ok=True)

    # Sanitizza l'URL per il nome del file
    sanitized_url = sanitize_filename(url)
    filename = f"{sanitized_url}.html"
    file_path = os.path.join(dir_path, filename)
    return file_path

def save_html_page(url, html_content):
    """
    Salva il contenuto HTML in un file strutturato in base al subreddit.

    Parametri:
    - url (str): L'URL della pagina
    - html_content (str): Il contenuto HTML da salvare

    Ritorna:
    - file_path (str): Il percorso del file salvato, o None in caso di errore
    """
    file_path = get_html_file_path(url)

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(html_content)
        logger.info(f"📄 HTML salvato in: {file_path}")
        return file_path
    except OSError as e:
        logger.error(f"❌ Errore nel salvataggio del file {file_path}: {e}")
        return None
