from bs4 import BeautifulSoup
import re
from scraper.logger_setup import setup_logger

logger = setup_logger("parser_logger", to_file=True, log_dir="app/parser/logger")

def extract_rules_from_wiki(html):
    soup = BeautifulSoup(html, "html.parser")
    rules = []

    seen = set()  # Evita duplicati

    # Caso 1: Tabella dopo <h1> "Rules"
    rules_header = soup.find("h1", string=re.compile(r"rules", re.I))
    if rules_header:
        table = rules_header.find_next("table")
        if table:
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) == 2:
                    title_raw = cols[0].get_text(strip=True)
                    desc_raw = cols[1].get_text(" ", strip=True)
                    rules.append((title_raw, desc_raw))

    # Caso 2: Lista <ul> o <ol> dentro <div class="md"> con <li>
    for div in soup.find_all("div", class_="md"):
        for li in div.find_all("li"):
            texts = li.stripped_strings
            text = " ".join(texts)
            match = re.match(r"(\d+)\.\s+(.*)", text)
            if match:
                title = match.group(2)
                desc = li.get_text(" ", strip=True).replace(match.group(0), "").strip()
                rules.append((title, desc))
            elif len(text) > 20:  # Evita rumore
                rules.append((text, ""))

    # Caso 3: Div layout strutturati (reddit redesign)
    for rule_block in soup.select('div.qib3ca-1'):
        title = rule_block.get_text(strip=True)
        desc_div = rule_block.find_next_sibling("div")
        desc = desc_div.get_text(" ", strip=True) if desc_div else ""
        if title:
            rules.append((title, desc))

    # Pulizia e numerazione
    final_rules = []
    for i, (title, desc) in enumerate(rules, start=1):
        key = (title.strip().lower(), desc.strip().lower())
        if key in seen:
            continue
        seen.add(key)
        final_rules.append({
            "number": i,
            "title": title.strip(),
            "description": desc.strip()
        })

    # Log finale
    if not final_rules:
        logger.warning("❌ Nessuna regola trovata.")
    else:
        for rule in final_rules:
            logger.info(f"Regola {rule['number']}. {rule['title']}")
            logger.info(f"Descrizione: {rule['description']}")
            logger.info("---")

    return final_rules
