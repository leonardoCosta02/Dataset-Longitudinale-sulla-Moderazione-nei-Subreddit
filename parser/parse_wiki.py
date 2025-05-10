from bs4 import BeautifulSoup
import re
from app.scraper.logger_setup import setup_logger
logger = setup_logger("parser_logger", to_file=True, log_dir="app/parser/logger")
def extract_rules_from_wiki(html):
    soup = BeautifulSoup(html, "html.parser")

    # Trova il titolo "Rules"
    rules_header = soup.find("h1", string=re.compile(r"rules", re.I))
    if not rules_header:
        return []

    # Trova la tabella immediatamente dopo il titolo "Rules"
    table = rules_header.find_next("table")
    if not table:
        return []

    rules = []
    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) != 2:
            continue
        title_raw = cols[0].get_text(strip=True)
        desc_raw = cols[1].get_text(" ", strip=True)

        # Estrai il numero se presente (es. "1. No memes")
        match = re.match(r"(\d+)\.\s+(.*)", title_raw)
        if match:
            number = int(match.group(1))
            title = match.group(2)
        else:
            number = None
            title = title_raw

        rules.append({
            "number": number,
            "title": title,
            "description": desc_raw
        })

        if not rules:
            logger.warning("Nessuna regola trovata.")
        else:
            for rule in rules:
                num = f"{rule['number']}." if rule['number'] is not None else "-"
                logger.info(f"Regola {num} {rule['title']}")
                logger.info(f"Descrizione: {rule['description']}")
                logger.info("---")

    return rules
