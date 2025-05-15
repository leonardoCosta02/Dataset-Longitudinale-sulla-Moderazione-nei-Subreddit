import pandas as pd #Serve a leggere e gestire i dati in tabella (il file .tsv con le frasi).
import re #Serve per usare le espressioni regolari (per pulire il testo).
from sklearn.model_selection import train_test_split #Serve per dividere il dataset in 80% per allenamento e 20% per test.
from sklearn.feature_extraction.text import TfidfVectorizer #Serve per trasformare il testo in numeri che il modello può capire (TF-IDF).
from sklearn.metrics import classification_report, precision_recall_curve #Serve per valutare quanto è bravo il modello con metriche come Precision, Recall, F1-score
import joblib #Serve a salvare il modello e il vettorizzatore su disco.
from scraper.logger_setup import setup_logger
logger = setup_logger("parser_logger", to_file=True, log_dir="parser/logger")
"""
Converte tutto in minuscolo

Rimuove link

Rimuove punteggiatura e simboli

Ritorna solo testo semplice e pulito

"""
def clean_text(text):
    """Pulisce e normalizza il testo rimuovendo link, punteggiatura e trasformando in minuscolo."""
    text = str(text).lower()
    text = re.sub(r"http\S+", "", text)  # Rimuove link
    text = re.sub(r"[^a-z0-9\s]", "", text)  # Rimuove punteggiatura
    return text.strip()
"""
XGBClassifier è una classe di XGBoost, una libreria potente e veloce per il machine learning, specializzata in compiti di classificazione e regressione.
I parametri che hai usato:
XGBClassifier(
    use_label_encoder=False,
    eval_metric='logloss',  misura quanto il modello sbaglia nella stima della probabilità.
    n_estimators=100, crea 100 alberi (più alberi = più accuratezza, ma più lenti)
    max_depth=4 ogni albero può andare fino a 4 livelli (controlla la complessità)
    )

Cos'è un albero decisionale?
Un albero decisionale è un modello che prende decisioni passo dopo passo, come se fosse un diagramma a blocchi.

✅ Nel tuo caso:
Serve a rispondere alla domanda:

“Questa frase è una regola oppure no?”
 
"Do not post personal information"
Il modello l’ha trasformata in un vettore numerico (TF-IDF), che indica:

Quanto pesano parole come “do not”, “personal”, “information”, ecc.

L’albero può decidere così:
Se "contains 'do not'" (peso alto) → vai a sinistra  
  Se "contains 'information'" (peso alto) → Classifica come: RULE
  Altrimenti → Classifica come: NON-RULE

Altrimenti → vai a destra  
  Se "contains 'welcome'" → NON-RULE  
  Altrimenti → RULE

Ogni nodo dell'albero controlla una condizione su una feature (es. “la parola ‘do not’ ha un certo peso?”)
Alla fine, le foglie ti dicono 0 = non-rule o 1 = rule.

XGBoost non usa un solo albero, ma costruisce molti alberi uno dopo l’altro, ognuno per correggere gli errori del precedente. Questo processo si chiama boosting.

Il primo albero prova a classificare.

Il secondo corregge gli errori del primo.

Il terzo corregge gli errori dei primi due.

…e così via, fino a 100 alberi (nel tuo caso).

XGBClassifier è perfetto per il tuo caso perché:
  gestisce bene grandi quantità di testo trasformato in numeri,
  ti permette di regolare la soglia di decisione,
  offre ottime performance per distinguere “regole vere” da frasi generiche
"""
from xgboost import XGBClassifier #Importa il classificatore XGBoost, molto usato e potente per problemi di classificazione.

def start_class():
    df = pd.read_csv("parser/sample_rules_dataset.tsv", sep="\t") #Carica il file TSV che contiene le frasi e le etichette.
    """
    Pulisce le frasi
    Rimuove spazi dalle etichette
    Converte “rule” → 1, “non-rule” → 0 (numeri per il modello)
    
    """
    df["text"] = df["text"].fillna("").apply(clean_text)
    df["label"] = df["label"].str.strip()
    df["binary_label"] = df["label"].map({"non-rule": 0, "rule": 1})

    df = df.sample(frac=1, random_state=42).reset_index(drop=True)#Mescola le righe del dataset in modo casuale.

    """
    Divide i dati:

    80% per addestrare (X_train, y_train) (usato per fargli "imparare")

    20% per testare (X_test, y_test) (usato per testare quanto è bravo)

    Quindi la valutazione viene fatta su dati dello stesso .tsv, ma che il modello non ha mai visto durante l’addestramento. 
    Questa è una pratica comune e si chiama train-test split
    """
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["binary_label"], test_size=0.2, random_state=42
    )
     
    #Converte ogni frase in un vettore di numeri basato su parole singole e coppie di parole (ngrammi).
    """
     max_features=60000 non appartiene a XGBClassifier, ma è un parametro del TfidfVectorizer, che viene usato per trasformare il testo in numeri prima di passarlo al modello.
     dice al vettorizzatore di tenere al massimo 60.000 parole (o coppie di parole) tra quelle più frequenti nel dataset.
     limita il numero massimo di termini che il tuo modello userà come "input numerici".
     Serve a controllare la complessità, velocizzare il training, e migliorare le performance.

     ngram_range=(1, 2) Estrai unigrammi (1 parola) e bigrammi (coppie di parole) dal testo. 
     1 = includi tutte le singole parole
     2 = includi anche tutte le coppie di parole consecutive

     "No personal attacks allowed"
      ["no", "personal", "attacks", "allowed"]
       
      ["no personal", "personal attacks", "attacks allowed"]

      come sono fatti i vettori creati dal TfidfVectorizer che vengono poi mandati al tuo modello XGBClassifier:
      Ogni frase viene trasformata in un vettore di numeri.
      Ogni numero rappresenta quanto è importante una parola (o coppia di parole) nella frase.
      "No personal attacks allowed"
      Con ngram_range=(1, 2) → il vettorizzatore crea un vocabolario come:
      ["no", "personal", "attacks", "allowed", "no personal", "personal attacks", "attacks allowed", ...]
      Supponiamo che abbiamo 60.000 di questi ngrammi nel vocabolario.
      Il vettore risultante:
      [0.0, 0.0, 0.348, 0.0, 0.612, ..., 0.0]  ← lunghezza: 60.000
      Ogni posizione rappresenta un termine del vocabolario.
      Il numero è il valore TF-IDF (quanto è importante quella parola/ngrams in questa frase rispetto al resto del dataset).
      Se un termine non è presente nella frase → valore = 0.
      TF-IDF sta per:

        TF = Term Frequency
        → Quante volte appare un termine in una frase (o documento)

        IDF = Inverse Document Frequency
        → Quanto è raro quel termine nel dataset complessivo (cioè tutte le frasi)
        Se una parola appare spesso nella frase = TF alto
        Se quella parola è poco comune nel resto del dataset = IDF alto
        Se entrambe le cose sono vere → TF-IDF alto
        Il modello non legge le parole. Ma quando riceve un vettore con valori alti per certi n-grammi importanti (es. “no memes”, “do not post”), può capire che questa frase è simile a una vera regola.






    """
   

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=60000)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    #Crea il modello XGBoost : Lo addestra con i dati X_train_vec (input) e y_train (etichetta)
    clf = XGBClassifier(use_label_encoder=False, eval_metric='logloss', n_estimators=100, max_depth=4)
    clf.fit(X_train_vec, y_train)

    #Calcola le probabilità che ogni frase sia una regola
    #Fa anche la predizione finale (0 o 1)
    y_probs = clf.predict_proba(X_test_vec)[:, 1]
    y_pred = clf.predict(X_test_vec)
    
    #Stampa un report: quante frasi ha classificato correttamente o sbagliato.
    """
    Accuracy:Percentuale di predizioni corrette su tutte le frasi del test.
             Ma attenzione: l’accuracy può essere fuorviante se i dati sono sbilanciati.
    
    Precision:“Di tutte le volte che ho detto 'è una regola', quante volte avevo ragione?”
              = true positive / (true positive + false positive)

    Recall:“Di tutte le vere regole nel dataset, quante ne ho riconosciute?”
           =  true positive / (true positive + false negative)
​    
    F1-score:Media armonica tra precision e recall. Utile per valutare un compromesso bilanciato tra entrambi.
             = 2*Precision+Recall/(Precision⋅Recal)
    
         
    
    """
    logger.info("\n📊 Report di classificazione:\n")
    logger.info(classification_report(y_test, y_pred))
    
    #Calcola la soglia ideale per dire “questa frase è una regola” (in base a precision e recall)
    precision, recall, thresholds = precision_recall_curve(y_test, y_probs)
    f1_scores = 2 * precision * recall / (precision + recall)
    best_threshold = thresholds[f1_scores.argmax()]

    #Questo serve a trovare la soglia di probabilità migliore (es. 0.562) per dire:“Da qui in poi considero la frase una regola”
    logger.info(f"\n⚙️ Soglia ottimale consigliata: {best_threshold:.3f}\n")

    #Salva il classificatore e il vettorizzatore, così il parser li può usare senza riallenare tutto ogni volta.
    joblib.dump(clf, "parser/rule_classifier_xgb.joblib")
    joblib.dump(vectorizer, "parser/rule_vectorizer_xgb.joblib")
    logger.info("\n✅ Modello XGBoost e vettorizzatore salvati.")


    