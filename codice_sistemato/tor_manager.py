import time  # Importa il modulo time per gestire i ritardi nel programma
import subprocess  # Importa il modulo subprocess per avviare processi esterni
from stem.control import Controller  # Importa Controller da stem per interagire con Tor
from stem import Signal  # Importa Signal da stem per inviare segnali a Tor
import requests  # Importa requests per effettuare richieste HTTP

# Definisce il dizionario dei proxy per Tor (socks5h è il protocollo per Tor)
PROXIES = {
    "http": "socks5h://127.0.0.1:9050",  # Proxy per HTTP
    "https": "socks5h://127.0.0.1:9050"  # Proxy per HTTPS
}

def start_tor():
    """Avvia Tor come processo separato.
    
    Questo avvia il processo Tor utilizzando il percorso del file eseguibile 
    di Tor e il file di configurazione torrc. Il processo viene eseguito in 
    background e viene atteso per 10 secondi affinché Tor si avvii correttamente.
    
    Ritorna:
    tor_process (Popen): Oggetto del processo Tor se l'avvio è riuscito, altrimenti None.
    """
    tor_path = "C:/Users/costa/OneDrive/Desktop/Tor Browser/Browser/TorBrowser/Tor/tor.exe"  # Percorso dell'eseguibile Tor
    torrc_path = "C:/Users/costa/OneDrive/Desktop/Tor Browser/Browser/TorBrowser/Data/Tor/torrc"  # Percorso del file di configurazione torrc
    
    try:
        # Avvia il processo Tor con i percorsi dati, reindirizzando l'output e l'errore in stdout e stderr
        tor_process = subprocess.Popen([tor_path, "-f", torrc_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(10)  # Attende 10 secondi per assicurarsi che Tor si avvii correttamente
        print("✅ Tor avviato.")
        return tor_process  # Ritorna il processo Tor se l'avvio è riuscito
    except Exception as e:
        print(f"❌ Errore nell'avvio di Tor: {e}")  # Gestisce eventuali errori durante l'avvio
        return None  # Ritorna None se c'è un errore

def change_ip():
    """Richiede a Tor un nuovo IP.
    
    Questo invia un segnale NEWNYM al controller Tor per richiedere un nuovo IP.
    Viene utilizzato il controller Tor sulla porta 9051 e autenticato prima di inviare il segnale.
    La funzione attende 10 secondi per consentire a Tor di cambiare l'IP.
    """
    try:
        with Controller.from_port(port=9051) as controller:  # Connessione al controller Tor sulla porta 9051
            controller.authenticate()  # Autenticazione con Tor
            print("Autenticazione riuscita!")  # Stampa conferma se l'autenticazione è riuscita
            controller.signal(Signal.NEWNYM)  # Invia il segnale per cambiare IP
            print("🔄 Cambiato IP Tor.")  # Stampa che l'IP è stato cambiato
            time.sleep(10)  # Attende 10 secondi per permettere al cambio IP di essere effettivo
    except Exception as e:
        print(f"❌ Errore nel cambio IP: {e}")  # Gestisce eventuali errori durante la richiesta di cambio IP

def get_ip():#Usata per fare test se cambiava effettivamente IP 
    """Recupera l'IP pubblico attuale utilizzando l'API del Tor Project.
    
    Questo invia una richiesta GET all'API pubblica del Tor Project per ottenere l'IP attuale che Tor sta utilizzando.
    Viene utilizzato il proxy Tor definito precedentemente per effettuare la richiesta.
    
    Ritorna:
    str: L'indirizzo IP pubblico corrente, o un messaggio di errore se si verifica un problema.
    """
    try:
        response = requests.get("https://check.torproject.org/api/ip", proxies=PROXIES, timeout=10)  # Invia la richiesta per ottenere l'IP
        return response.json().get("IP", "Errore nel recupero dell'IP")  # Ritorna l'IP estratto dalla risposta JSON
    except Exception as e:
        return f"Errore nel recupero dell'IP: {e}"  # Ritorna un messaggio di errore se si verifica un problema con la richiesta
