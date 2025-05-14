import pandas as pd
import re
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
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

from xgboost import XGBClassifier

def start_class():
    df = pd.read_csv("parser/sample_rules_dataset.tsv", sep="\t")
    df["text"] = df["text"].fillna("").apply(clean_text)
    df["label"] = df["label"].str.strip()
    df["binary_label"] = df["label"].map({"non-rule": 0, "rule": 1})
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["binary_label"], test_size=0.2, random_state=42
    )
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=60000)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    clf = XGBClassifier(use_label_encoder=False, eval_metric='logloss', n_estimators=100, max_depth=4)
    clf.fit(X_train_vec, y_train)
    y_probs = clf.predict_proba(X_test_vec)[:, 1]
    y_pred = clf.predict(X_test_vec)
    logger.info("\n📊 Report di classificazione:\n")
    logger.info(classification_report(y_test, y_pred))
    precision, recall, thresholds = precision_recall_curve(y_test, y_probs)
    f1_scores = 2 * precision * recall / (precision + recall)
    best_threshold = thresholds[f1_scores.argmax()]
    logger.info(f"\n⚙️ Soglia ottimale consigliata: {best_threshold:.3f}\n")
    joblib.dump(clf, "parser/rule_classifier_xgb.joblib")
    joblib.dump(vectorizer, "parser/rule_vectorizer_xgb.joblib")
    logger.info("\n✅ Modello XGBoost e vettorizzatore salvati.")


    