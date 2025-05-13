import pandas as pd
import joblib
from sklearn.metrics import classification_report

# === CONFIGURAZIONE ===
TSV_FILE = "app/parser/sample_rules_dataset.tsv"           # <== Cambia con il tuo percorso
CLASSIFIER_FILE = "app/parser/rule_classifier.joblib"
VECTORIZER_FILE = "app/parser/rule_vectorizer.joblib"
THRESHOLD = 0.5                                  # <== Cambia la soglia qui
OUTPUT_FILE = "app/parser/classified_rules_with_probs.tsv"

# === CARICAMENTO ===
print("📦 Caricamento modello e vettorizzatore...")
clf = joblib.load(CLASSIFIER_FILE)
vectorizer = joblib.load(VECTORIZER_FILE)

print(f"📄 Lettura del dataset: {TSV_FILE}")
df = pd.read_csv(TSV_FILE, sep="\t").dropna()
df["text"] = df["text"].str.strip()

# === VETTORIZZAZIONE ===
X = vectorizer.transform(df["text"])
probs = clf.predict_proba(X)

# === CLASSIFICAZIONE ===
df["prob_rule"] = probs[:, 1]
df["predicted_label"] = df["prob_rule"].apply(lambda p: "rule" if p >= THRESHOLD else "non-rule")

# === REPORT ===
print("\n📊 REPORT di classificazione:\n")
print(classification_report(df["label"], df["predicted_label"]))

# === SALVATAGGIO ===
df.to_csv(OUTPUT_FILE, sep="\t", index=False)
print(f"\n✅ File salvato: {OUTPUT_FILE}")
