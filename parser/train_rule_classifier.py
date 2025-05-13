import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import joblib
# 🔹 Carica il dataset TSV contenente regole e non-regole
# Il file deve avere almeno le colonne: 'text' e 'label'
df = pd.read_csv("app/parser/sample_rules_dataset.tsv", sep="\t")

# 🔹 Rimuove eventuali valori nulli e normalizza gli spazi
# (può servire se ci sono campi vuoti o spazi sporchi)
df["text"] = df["text"].fillna("").str.strip()

# 🔹 Divide il dataset in training (80%) e test (20%)
X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["label"], test_size=0.2, random_state=42
)

# 🔹 Crea un trasformatore TF-IDF per convertire il testo in numeri
# - Usa un n-gramma tra 1 e 2 (singole parole + coppie)
# - Limita le feature a 2000 termini più rilevanti
vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=2000)
X_train_vec = vectorizer.fit_transform(X_train)  # Applica fit+transform al training set
X_test_vec = vectorizer.transform(X_test)        # Solo transform al test set

# 🔹 Addestra un classificatore di regressione logistica
# - max_iter alto per evitare warning di convergenza
clf = LogisticRegression(max_iter=1000)
clf.fit(X_train_vec, y_train)

# 🔹 Valuta il classificatore sul test set
# - Mostra precision, recall, F1 per ogni classe (rule / non-rule)
y_pred = clf.predict(X_test_vec)
print("\n📊 Report di classificazione:\n")
print(classification_report(y_test, y_pred))

# 🔹 Salva il classificatore e il vettorizzatore su file
# - Questi file saranno usati per la predizione nel parser
joblib.dump(clf, "app/parser/rule_classifier.joblib")
joblib.dump(vectorizer, "app/parser/rule_vectorizer.joblib")

print("\n✅ Modello e vettorizzatore salvati.")
