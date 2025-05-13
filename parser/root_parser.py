import re
import os
from parser.parse_homepage import parse_rules_from_html
from parser.parse_old_homepage import parse_rules_from_old_html
from parser.parse_mod import extract_moderators
from parser.parse_wiki import extract_rules_from_wiki
from scraper.logger_setup import setup_logger

logger = setup_logger("parser_logger", to_file=True, log_dir="parser/logger")


def root_parser(doc):
    url = doc.get("subreddit", "")
    subreddit = extract_subreddit_name(url)
    logger.info(f"Url estratto: {url}")

    if not subreddit:
        logger.warning("❌ Subreddit URL non valido.")
        return None

    file_path = doc.get("file_path")
    if not file_path:
        logger.warning("❌ Nessun 'file_path' presente nel documento.")
        return None

    if not os.path.isfile(file_path):
        logger.warning(f"❌ File non trovato nel container: {file_path}")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            logger.info(f"📄 Inizio parsing file: {file_path}")
            html_content = file.read()
    except Exception as e:
        logger.error(f"❌ Errore apertura file: {e}")
        return None

    # Riconoscimento tipo di pagina
    patterns = {
        "moderators": re.compile(rf"https?://(www\.)?reddit\.com/r/{subreddit}/about/moderators/?$"),
        "wiki": re.compile(rf"https?://(www\.)?reddit\.com/r/{subreddit}/wiki/index/?$"),
        "homepage": re.compile(rf"https?://(www\.)?reddit\.com/r/{subreddit}/?$"),
        "homepage_old": re.compile(rf"https?://(old\.)?reddit\.com/r/{subreddit}/?$"),
        "moderators_old": re.compile(rf"https?://(old\.)?reddit\.com/r/{subreddit}/about/moderators/?$")
    }

    if patterns["moderators"].match(url) or patterns["moderators_old"].match(url):
        return extract_moderators(html_content)
    elif patterns["wiki"].match(url):
        return extract_rules_from_wiki(html_content)
    elif patterns["homepage"].match(url):
        return parse_rules_from_html(html_content)
    elif patterns["homepage_old"].match(url):
        return parse_rules_from_old_html(html_content)
    else:
        logger.warning("⚠️ URL non corrisponde a nessun pattern noto.")
        return None


def extract_subreddit_name(url):
    """Estrae il nome del subreddit da un URL"""
    match = re.search(r"/r/([^/]+)", url)
    return match.group(1) if match else None
