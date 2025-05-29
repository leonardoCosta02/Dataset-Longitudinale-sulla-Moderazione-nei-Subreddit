# 🧠 Dataset Longitudinale sulla Moderazione nei Subreddit

Questo progetto di tesi sviluppa un **sistema automatizzato** per la raccolta, archiviazione e parsing di snapshot storici di subreddit pubblici, al fine di costruire un **dataset longitudinale replicabile** per l’analisi retrospettiva della moderazione online.

---

## 📚 Obiettivi

- Raccogliere snapshot HTML semestrali di subreddit dal 2012 al 2024 tramite le API della **Wayback Machine**
- Estrarre informazioni su **moderatori** e **regole** da HTML storici
- Validare e filtrare automaticamente le regole con un **modello ML**
- Archiviare i dati in modo strutturato (MongoDB + cache HTML locale)

---

## 🛠️ Tecnologie utilizzate

- Python 3.10+
- MongoDB
- Docker + Docker Compose
- BeautifulSoup, requests, joblib
- XGBoost + Scikit-learn
- Wayback Machine API

---

## 📦 Struttura della repository

```
.
├── main.py                     # Scraper principale
├── main_parser.py             # Parser principale
├── scraper/                   # Logica scraping
│   ├── scraper.py
│   ├── wayback_client.py
│   ├── utils.py
│   ├── logger_setup.py
├── parser/                    # Parsing e ML
│   ├── root_parser.py
│   ├── parse_homepage.py
│   ├── parse_old_homepage.py
│   ├── parse_mod.py
│   ├── parse_wiki.py
│   ├── train_rule_classifier.py
│   ├── rule_classifier_xgb.joblib
│   ├── rule_vectorizer_xgb.joblib
├── db/
│   ├── database.py
├── html_cache/                # File HTML archiviati
├── logs/                      # Log di scraping/parsing
├── sample_rules_dataset.tsv  # Dataset etichettato per il training
├── embedding-metadata.tsv    # Lista dei subreddit target
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
```

---

## ⚙️ Setup e utilizzo

### 🔁 Avvio automatico via Docker

```bash
docker-compose up --build
```

Avvia MongoDB e l’intero sistema di scraping e parsing all’interno di un container.



## 🧠 Parsing & Classificazione delle Regole

### 🔍 Riconoscimento Layout
Il modulo `root_parser.py` analizza il tipo di pagina:
- `wiki` → `parse_wiki.py`
- `homepage` → `parse_homepage.py`
- `old homepage` → `parse_old_homepage.py`
- `moderators` → `parse_mod.py`

Ogni parser è in grado di gestire layout HTML diversi grazie a funzioni mirate (case 1–11).

### 🤖 Classificatore ML

Il file `train_rule_classifier.py` addestra un modello **XGBoost** per distinguere vere regole da contenuti generici.

- Dataset: `sample_rules_dataset.tsv`
- TF-IDF con unigrammi e bigrammi
- Output: `rule_classifier_xgb.joblib` + `rule_vectorizer_xgb.joblib`
- Soglia configurabile (default: `0.105`)

---

## 📤 Output

### 🔸 Collezione `cache` (input)
```json
{
  "_id": "https://web.archive.org/web/202307.../r/funny",
  "file_path": "html_cache/fun/...html",
  "subreddit": "https://www.reddit.com/r/funny/",
  "snapshot_year": 2023,
  "semester": "S1",
  "da_parsare": true
}
```

### 🔹 Collezione `regole`
```json
{
  "_id": "https://web.archive.org/web/2023.../r/funny",
  "regole": [
    { "title": "No politics" },
    { "title": "Memes go to /r/AdviceAnimals" }
  ]
}
```

### 🔸 Collezione `moderatori`
```json
{
  "_id": "https://web.archive.org/web/2023.../r/funny",
  "moderatori": [
    { "username": "mod123", "karma": 1240, "timestamp": "2023-07-01T12:00:00Z" }
  ]
}
```

---

## 📊 Analisi possibile con il dataset

- Evoluzione delle **policy di moderazione**
- Cambiamento nei **moderatori e permessi**
- Analisi **longitudinale** di trend comunitari
- Addestramento di **sistemi automatici di rilevamento regole**

---

## 🔒 Licenza

Questo progetto è distribuito con licenza **MIT**.

---

## 👤 Autore

**Leonardo Costantini**  
GitHub: [@leonardoCosta02](https://github.com/leonardoCosta02)  
