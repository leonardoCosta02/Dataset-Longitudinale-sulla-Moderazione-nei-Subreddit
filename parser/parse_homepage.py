from scraper.logger_setup import setup_logger
from bs4 import BeautifulSoup  # Importa BeautifulSoup per il parsing dei file HTML
import re  # Importa il modulo delle espressioni regolari per pattern matching
import joblib
clf = joblib.load("parser/rule_classifier_xgb.joblib")
vectorizer = joblib.load("parser/rule_vectorizer_xgb.joblib")
logger = setup_logger("parser_logger", to_file=True, log_dir="parser/logger")
# ----------- PARSER CASE 1 -----------
# Estrae regole da una lista <ul> situata in una posizione precisa del DOM
def parse_case_1(soup):
    """
    Estrae le regole da una lista <ul> all'interno del form.
    Ogni <li> contiene un <p> con il testo della regola.
    """
    ul = soup.select_one('form > div > div > ul:nth-child(7)')  # Seleziona la settima lista <ul> nel form
    rules = []  # Lista delle regole estratte
    if ul:  # Se la lista è stata trovata
        for li in ul.find_all('li'):  # Per ogni elemento <li> della lista
            p = li.find('p')  # Cerca un paragrafo all'interno del <li>
            if p:  # Se il paragrafo esiste
                text = p.get_text(strip=True)  # Ottieni il testo rimuovendo spazi
                rules.append(text)  # Aggiungi la regola alla lista
    return rules  # Ritorna la lista di regole

# ----------- PARSER CASE 2 -----------
def parse_case_2(soup):
    """
    Simile al caso 1 ma cerca la decima lista <ul>.
    """
    rules = []
    ul = soup.select_one('form > div > div > ul:nth-child(10)')  # Seleziona la decima lista
    if ul:
        for li in ul.find_all('li'):
            p = li.find('p')
            if p:
                text = p.get_text(strip=True)
                rules.append(text)
    return rules

# ----------- PARSER CASE 3 -----------
def parse_case_3(soup):
    """
    Estrae regole da una lista ordinata <ol>.
    """
    rules = []
    ol = soup.select_one('form> div > div > ol')  # Seleziona la lista <ol>
    if ol:
        for li in ol.find_all('li'):
            p = li.find('p')
            if p:
                text = p.get_text(strip=True)
                rules.append(text)
    return rules

# ----------- PARSER CASE 4 -----------
def parse_case_4(soup):
    """
    Cerca un <h1> con 'rules' e raccoglie i <h2> successivi finché non trova un altro <h1>.
    """
    h1 = soup.find('h1', string=lambda t: t and "rules" in t.lower())  # Trova <h1> contenente 'rules'
    rules = []
    if h1:
        for tag in h1.find_all_next():  # Itera sui tag successivi
            if tag.name == "h2":  # Se è un <h2>
                rule = tag.get_text(strip=True)
                if rule:
                    rules.append(rule)
            elif tag.name and tag.name.startswith("h1"):  # Se incontra un altro <h1>, si ferma
                break
    return rules

# ----------- PARSER CASE 5 -----------
def parse_case_5(soup):
    """
    Cerca <h1> con 'rules' e legge tutti i paragrafi nel primo <blockquote> successivo.
    """
    rules = []
    h1 = soup.find('h1', string=lambda s: s and 'rules' in s.lower())
    if h1:
        blockquote = h1.find_next('blockquote')  # Trova primo blockquote dopo <h1>
        if blockquote:
            for p in blockquote.find_all('p'):
                rule_text = p.get_text(separator=' ', strip=True)
                if rule_text:
                    rules.append(rule_text)
    return rules

# ----------- PARSER CASE 6 -----------
def parse_case_6(soup):
    """
    Cerca una tabella subito dopo <h1> con 'rules', combinando titolo e descrizione di ogni riga.
    """
    h1 = soup.find('h1', string=lambda t: t and "rules" in t.lower())
    rules = []
    if h1:
        table = h1.find_next('table')  # Trova tabella successiva a <h1>
        if table:
            for row in table.find_all('tr'):
                cols = row.find_all('td')
                if cols:
                    titolo = cols[0].get_text(strip=True)
                    descrizione = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                    full_text = f"{titolo} - {descrizione}" if descrizione else titolo
                    rules.append(full_text)
    return rules

# ----------- PARSER CASE 7 -----------
def parse_case_7(soup):
    """
    Estrae regole da <div> con classi specifiche (esempio design Reddit).
    """
    rules = []
    for div in soup.select("div._8ZLJI1-ZiP7pHJ_yO1L4Z._3osxlOKfiylmgqNqsW7erB"):
        text = div.select_one("div.tbIApBd2DM_drfZQJjIum")
        if text:
            rules.append(text.get_text(strip=True))
    return rules

# ----------- PARSER CASE 8 -----------
def parse_case_8(soup):
    """
    Simile al caso 7 ma con altre classi CSS (variante del frontend).
    """
    rules = []
    for div in soup.select("div.s1i3808h-2.ckCcrs"):
        text = div.select_one("div.s1i3808h-4.eBcdMM")
        if text:
            rules.append(text.get_text(strip=True))
    return rules

# ----------- PARSER CASE 9 -----------
def parse_case_9(soup):
    """
    Cerca <h1> con 'rules' e prende la <ul> successiva.
    """
    rules = []
    for h1 in soup.find_all("h1"):
        if "rules" in h1.get_text(strip=True).lower():
            current = h1.find_next_sibling()
            while current:
                if hasattr(current, 'name') and current.name == "ul":
                    for li in current.find_all("li"):
                        text = li.get_text(strip=True)
                        if text:
                            rules.append(text)
                    break
                current = current.find_next_sibling()
            break
    return rules

# ----------- PARSER CASE 10 -----------
def parse_case_10(soup):
    """
    Cerca heading (h1/h2/h3) con 'rules' e prende <ol> successiva.
    """
    heading = soup.find(lambda tag: tag.name in ['h1', 'h2', 'h3'] and 'rules' in tag.get_text(strip=True).lower())
    rules = []
    if heading:
        ol = heading.find_next('ol')
        if ol:
            for li in ol.find_all('li'):
                
                    text = li.get_text(strip=True)
                    if text:
                        rules.append(text)
    return rules

# ----------- PARSER CASE 11 -----------
def parse_case_11(soup):
    """
    Estrae <div> il cui testo inizia con numero (es. '1. Regola').
    """
    return [div.get_text(strip=True) for div in soup.find_all('div') if re.match(r"^\s*\d+[\.\)]\s+", div.get_text(strip=True))]

# ----------- FUNZIONE PRINCIPALE CON ML -----------
def parse_rules_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    parsing_functions = [
        parse_case_1, parse_case_2, parse_case_3, parse_case_4,
        parse_case_5, parse_case_6, parse_case_7, parse_case_8, 
        parse_case_9, parse_case_10, parse_case_11
    ]
    for i, func in enumerate(parsing_functions, start=1):
        rules = func(soup)
        filtered_rules = []
        rejected_rules = []

        for r in rules:
            if _is_likely_rule(r):
                filtered_rules.append(r)
            else:
                rejected_rules.append(r)

        if filtered_rules:
            logger.info(f"✅ Caso {i} selezionato:")
            for j, rule in enumerate(filtered_rules, start=1):
                logger.info(f"Regola {j}: {rule}")
            if rejected_rules:
                logger.info("⚠️ Regole escluse dal classificatore ML:")
                for r in rejected_rules:
                    logger.info(f"❌ Scartata: {r}")
            return filtered_rules

    logger.warning("❌ Nessuna regola trovata in nessun caso.")
    return []

def _is_likely_rule(text, threshold=0.562):
    vec = vectorizer.transform([text.strip()])
    prob = clf.predict_proba(vec)[0][1]
    logger.info(f"💡 Valutazione ML: '{text[:50]}...' → Probabilità: {prob:.3f}")
    return prob >= threshold
