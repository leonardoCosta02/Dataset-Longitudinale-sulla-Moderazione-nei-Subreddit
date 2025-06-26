from bs4 import BeautifulSoup
from scraper.logger_setup import setup_logger
import joblib

# Carica il classificatore e il vettorizzatore
clf = joblib.load("parser/rule_classifier_xgb.joblib")
vectorizer = joblib.load("parser/rule_vectorizer_xgb.joblib")
logger = setup_logger("parser_logger", to_file=True, log_dir="parser/logger")

def extract_rules_from_wiki(html):
    soup = BeautifulSoup(html, "html.parser")
    rules = []
    seen = set()

    def add_rule(title, desc):
        rules.append((title.strip(), desc.strip()))

    rules_found = False

    # 🔹 Cerca nel primo <div class="md">
    md_div = soup.find("div", class_="md")
    if md_div:
        # 🔹 Caso 1: PRIMA tabella dopo header con "rule" dentro <div class="md">
        header = md_div.find(["h1", "h2", "h3", "h4", "h5"], string=lambda s: s and "rule" in s.lower())
        if header:
            table = header.find_next("table")
            if table and md_div in table.parents:
                for row in table.find_all("tr"):
                    cols = row.find_all("td")
                    if len(cols) == 2:
                        title = cols[0].get_text(strip=True)
                        desc = cols[1].get_text(" ", strip=True)
                        add_rule(title, desc)
                if rules:
                    rules_found = True

        # 🔹 Caso 2: PRIMA lista dopo header con "rule" dentro <div class="md">
        if not rules_found and header:
            lst = header.find_next(["ul", "ol"])
            if lst and md_div in lst.parents:
                for li in lst.find_all("li", recursive=False):
                    strong = li.find("strong")
                    if strong:
                        title = strong.get_text(strip=True)
                        desc = li.get_text(" ", strip=True).replace(title, "").strip()
                        add_rule(title, desc)
                        continue

                    a_tag = li.find("a")
                    if a_tag:
                        title = a_tag.get_text(strip=True)
                        desc = li.get_text(" ", strip=True).replace(title, "").strip()
                        add_rule(title, desc)
                        continue

                    full = li.get_text(" ", strip=True)
                    if len(full) > 10:
                        add_rule(full, "")
                if rules:
                    rules_found = True

 # 🔍 Classificazione ML delle regole
    filtered_rules = []
    rejected_rules = []

    for t, d in rules:
        if _is_likely_rule(t, d):
            filtered_rules.append((t, d))
        else:
            rejected_rules.append((t, d))

    if rejected_rules:
        logger.info("⚠️ Regole escluse dal classificatore ML:")
        for t, d in rejected_rules:
            logger.info(f"❌ Scartata: {t} {d}")

    return _finalize_rules(filtered_rules, seen)

def _is_likely_rule(title, description, threshold=0.105):
    text = f"{title} {description}".strip()
    vec = vectorizer.transform([text])
    prob = clf.predict_proba(vec)[0][1]  # probabilità della classe "rule"
    logger.info(f"💡 Valutazione ML: '{text[:50]}...' → Probabilità: {prob:.3f}")
    return prob >= threshold

def _finalize_rules(rules, seen):
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

    if not final_rules:
        logger.warning("❌ Nessuna regola trovata.")
    else:
        for rule in final_rules:
            logger.info(f"✅ Regola {rule['number']}: {rule['title']}")
            logger.info(f"Descrizione: {rule['description']}")
            logger.info("---")

    return final_rules
