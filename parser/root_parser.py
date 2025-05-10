import re
from app.parser.parse_homepage import parse_rules_from_html
from app.parser.parse_mod import extract_moderators
from app.parser.parse_wiki import extract_rules_from_wiki
from app.scraper.logger_setup import setup_logger 
import os  # Importa os per la gestione dei percorsi dei file
logger = setup_logger("parser_logger", to_file=True, log_dir="app/parser/logger")
# ----------- PERCORSO BASE PROGETTO -----------
BASE_DIR = r"C:\Users\costa\OneDrive\Desktop\Tesi\codice_sistemato _Copia3\app"
def resolve_path(container_path: str) -> str:
    """
    Converte un percorso Docker (es. /app/...) in percorso Windows locale.
    """
    if not container_path.startswith("/app/"):
        raise ValueError(f"Path non valido (atteso che inizi con /app/): {container_path}")
    relative_path = container_path[len("/app/"):]
    real_path = os.path.join(BASE_DIR, *relative_path.split("/"))
    return real_path

def root_parser(doc):
    url = doc.get("subreddit", "")
    subreddit = extract_subreddit_name(url)
    logger.info(f"Url estratto: {url}")
   
    if not subreddit:
        logger.warning("error: Invalid subreddit URL")
        return None
    
    file_path = doc.get("file_path")

    if not file_path:
        logger.warning("[!] Nessun file_path nel documento")
        return None
                
    try:
        real_path = resolve_path(file_path)
    except ValueError as e:
            logger.warning(f"[!] Errore nel path: {e}")
            return None
                
    if not os.path.isfile(real_path):
        logger.warning(f"[!] File non trovato: {real_path}")
        return None
                
    try:
        with open(real_path, "r", encoding="utf-8") as file:
            logger.info(f"Inizio a parsare il file {real_path}")
            html_content = file.read()
                    
    except Exception as e:
        logger.error(f"[!] Errore leggendo il file: {e}")
        return None
    
    

    # Costruzione regex dinamica
    patterns = {
        "moderators": re.compile(rf"https?://(www\.)?reddit\.com/r/{subreddit}/about/moderators/?$"),
        "wiki": re.compile(rf"https?://(www\.)?reddit\.com/r/{subreddit}/wiki/index/?$"),
        "homepage": re.compile(rf"https?://(www\.)?reddit\.com/r/{subreddit}/?$"),
    }
    
    

    

    if patterns["moderators"].match(url):
        
        return extract_moderators(html_content)
    elif patterns["wiki"].match(url):
        return extract_rules_from_wiki(html_content)
    elif patterns["homepage"].match(url):
        return parse_rules_from_html(html_content)
    else:
        logger.warning("warning: URL does not match any known pattern")
        return None

def extract_subreddit_name(url):
    """Estrae il nome del subreddit da un URL valido"""
    match = re.search(r"/r/([^/]+)", url)
    return match.group(1) if match else None
