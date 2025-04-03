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
from scraper import download_page
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
        
        # Scarica la prima e la seconda pagina utilizzando la funzione esterna
        download_page(snapshot_urls, first_page, first_month, second_page, second_month, collection)
        download_page(snapshot_urls, second_page, second_month, first_page, first_month, collection)
        
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
