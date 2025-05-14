import pandas as pd
import re
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, precision_recall_curve
import joblib
from scraper.logger_setup import setup_logger
logger = setup_logger("parser_logger", to_file=True, log_dir="parser/logger")
def clean_text(text):
    """Pulisce e normalizza il testo rimuovendo link, punteggiatura e trasformando in minuscolo."""
    text = str(text).lower()
    text = re.sub(r"http\S+", "", text)  # Rimuove link
    text = re.sub(r"[^a-z0-9\s]", "", text)  # Rimuove punteggiatura
    return text.strip()

def start_class():
    # 🔹 Carica il dataset TSV contenente regole e non-regole
    df = pd.read_csv("parser/sample_rules_dataset.tsv", sep="\t")

    # 🔹 Pulisce e normalizza il testo
    df["text"] = df["text"].fillna("").apply(clean_text)
    df["label"] = df["label"].str.strip()

    # 🔹 Mappa i label a valori binari
    df["binary_label"] = df["label"].map({"non-rule": 0, "rule": 1})

    # 🔹 Divide il dataset in training (80%) e test (20%)
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["binary_label"], test_size=0.2, random_state=42
    )

    # 🔹 Trasformatore TF-IDF con ngrammi da 1 a 2 e 10000 feature massime
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=50000)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # 🔹 Classificatore Logistic Regression
    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    clf.fit(X_train_vec, y_train)

    # 🔹 Valutazione e report
    y_probs = clf.predict_proba(X_test_vec)[:, 1]
    y_pred = clf.predict(X_test_vec)
    logger.info("\n📊 Report di classificazione:\n")
    logger.info(classification_report(y_test, y_pred))

    # 🔹 Calcolo soglia ottimale basata su F1-score
    precision, recall, thresholds = precision_recall_curve(y_test, y_probs)
    f1_scores = 2 * precision * recall / (precision + recall)
    best_threshold = thresholds[f1_scores.argmax()]
    logger.info(f"\n⚙️ Soglia ottimale consigliata: {best_threshold:.3f}\n")

    # 🔹 Salvataggio del modello e del vettorizzatore
    joblib.dump(clf, "parser/rule_classifier.joblib")
    joblib.dump(vectorizer, "parser/rule_vectorizer.joblib")
    logger.info("\n✅ Modello e vettorizzatore salvati.")
