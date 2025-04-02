import os  # Importa il modulo os per interagire con il filesystem (per creare cartelle, gestire file, ecc.)
from pymongo import MongoClient  # Importa il client di MongoDB per interagire con il database
import sys  # Modulo per interagire con il sistema (come terminare il programma)
from concurrent.futures import ThreadPoolExecutor  # Importa ThreadPoolExecutor per eseguire operazioni in parallelo
import time  # Modulo per gestire le operazioni temporali (es. sleep)
import random  # Modulo per generare numeri casuali
import requests  # Modulo per fare richieste HTTP
from database import insert_html_document  # Funzione per inserire documenti HTML nel database
from scraper import get_snapshot_urls  # Funzione per recuperare gli snapshot da Wayback Machine
from utils import get_valid_snapshot  # Funzione per filtrare gli snapshot validi
from tor_manager import PROXIES  # Proxy per Tor
import scraper  # Modulo per il scraping
from utils import save_html_page  # Funzione per salvare una pagina HTML
from tor_manager import start_tor  # Funzione per avviare Tor

def scrape_snapshots(url):
    """Funzione principale che esegue lo scraping degli snapshot per un URL dato.
    
    Questa funzione recupera gli snapshot storici di una pagina web utilizzando Wayback Machine.
    Salva i risultati nel database MongoDB e gestisce la rotazione degli IP tramite Tor.
    
    Parametri:
    - url (str): L'URL della pagina web da cui recuperare gli snapshot.
    """
    subreddit_home = "/".join(url.split("/")[:5]) + "/"  # Calcola l'URL della home del subreddit
    print(f"Tor è attivo, avvio scraping per {url}...")
    
    for year in range(2012, 2025):  # Loop per ogni anno dal 2012 al 2024
        snapshot_urls = get_snapshot_urls(url, year)  # Recupera gli snapshot per l'anno
        if not snapshot_urls:
            print(f"{year}: Nessun snapshot per {url}, provo con la home {subreddit_home}")
            snapshot_urls = get_snapshot_urls(subreddit_home, year)  # Prova con la home del subreddit
        
        if not snapshot_urls:
            print(f"{year}: Nessun snapshot disponibile per {url} né per la home {subreddit_home}")
            continue  # Passa all'anno successivo se non ci sono snapshot
        
        # Recupera il primo e secondo snapshot validi per i semestri
        first_page, first_month = get_valid_snapshot(snapshot_urls, 1, 6)
        second_page, second_month = get_valid_snapshot(snapshot_urls, 7, 12)
        
        attempts_page1 = 0  # Contatore per i tentativi di recupero della prima pagina
        attempts_page2 = 0  # Contatore per i tentativi di recupero della seconda pagina
        
        # Controllo errore 403 per first_page
        while first_page:
            try:
                response = requests.get(first_page, proxies=PROXIES if scraper.use_proxy else None, timeout=15)  # Fai una richiesta HTTP per la prima pagina
                response.raise_for_status()  # Solleva un'eccezione se la risposta non è valida
                
                # Verifica se la distanza tra le due pagine è di almeno 4 mesi
                if second_page and abs(second_month - first_month) >= 4:
                    file_path = save_html_page(first_page, response.text)  # Salva la pagina HTML
                    insert_html_document(first_page, file_path, collection)  # Inserisci il documento nel database
                    time.sleep(5)  # Pausa per evitare sovraccarico del server
                else:
                    print(f"Salto {first_page} perché troppo vicino a {second_page}")
                break  # Esci dal ciclo se la pagina è stata scaricata correttamente
            except requests.RequestException as e:  # Gestisci eventuali errori nelle richieste
                print(f"Errore nel recupero di {first_page} prendo prossima pagina: {e}")
                attempts_page1 += 1  # Incrementa il contatore dei tentativi
                snapshot_urls.remove(first_page)  # Rimuovi la pagina dalla lista degli snapshot
                if attempts_page1 < 3:
                    first_page, first_month = get_valid_snapshot(snapshot_urls, 1 + attempts_page1, 6)  # Prova a ottenere il prossimo snapshot valido
                else:
                    print("Tutte le pagine sono forbidden, non recupero pagina per questo semestre")
                    break  # Interrompe il ciclo se ci sono troppi errori
        
        # Controllo errore 403 per second_page
        while second_page:
            try:
                response = requests.get(second_page, proxies=PROXIES if scraper.use_proxy else None, timeout=15)  # Fai una richiesta HTTP per la seconda pagina
                response.raise_for_status()  # Solleva un'eccezione se la risposta non è valida
                
                # Verifica se la distanza tra le due pagine è di almeno 4 mesi
                if first_page and abs(second_month - first_month) >= 4:
                    file_path = save_html_page(second_page, response.text)  # Salva la pagina HTML
                    insert_html_document(second_page, file_path, collection)  # Inserisci il documento nel database
                    time.sleep(5)  # Pausa per evitare sovraccarico del server
                else:
                    print(f"Salto {second_page} perché troppo vicino a {first_page}")
                break  # Esci dal ciclo se la pagina è stata scaricata correttamente
            except requests.RequestException as e:  # Gestisci eventuali errori nelle richieste
                print(f"Errore nel recupero di {second_page} prendo prossima pagina: {e}")
                attempts_page2 += 1  # Incrementa il contatore dei tentativi
                snapshot_urls.remove(second_page)  # Rimuovi la pagina dalla lista degli snapshot
                if attempts_page2 < 3:
                    second_page, second_month = get_valid_snapshot(snapshot_urls, 7 + attempts_page2, 12)  # Prova a ottenere il prossimo snapshot valido
                else:
                    print("Tutte le pagine sono forbidden, non recupero pagina per questo semestre")
                    break  # Interrompe il ciclo se ci sono troppi errori
        
        time.sleep(random.uniform(2, 5))  # Pausa casuale tra le richieste per evitare di sembrare un bot
    tor_process.kill()  # Uccide il processo Tor quando tutto lo scraping è completato

if __name__ == "__main__":
    # Connessione al database MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["reddit_db"]  # Seleziona il database
    collection = db["subreddit_html"]  # Seleziona la collezione per salvare i dati
    
    CACHE_DIR = "html_cache"  # Cartella per il salvataggio delle pagine HTML
    os.makedirs(CACHE_DIR, exist_ok=True)  # Crea la cartella se non esiste
    
    # Avvio del processo Tor per la rotazione degli IP
    tor_process = start_tor()
    if not tor_process:
        print("Impossibile avviare Tor. Uscita...")
        sys.exit()  # Esce se Tor non può essere avviato
    
    # Richiesta degli URL da analizzare
    urls = input("Inserisci gli URL da analizzare separati da uno spazio: ").split()
    
    # Esecuzione dello scraping in parallelo utilizzando ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.map(scrape_snapshots, urls)  # Mappa gli URL da analizzare e avvia lo scraping in parallelo
