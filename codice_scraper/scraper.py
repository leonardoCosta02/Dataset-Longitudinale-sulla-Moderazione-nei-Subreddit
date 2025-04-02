import requests  # Importa il modulo requests per fare richieste HTTP
from tor_manager import get_ip, change_ip, PROXIES  # Importa funzioni per gestire Tor e l'IP

import urllib3  # Importa il modulo urllib3 per la gestione delle connessioni HTTP

use_proxy = True  # Variabile globale che determina se usare o meno il proxy (Tor)

def get_snapshot_urls(url, year):
    """Recupera gli snapshot di un URL per un dato anno
    
    Questa funzione utilizza l'API della Wayback Machine per ottenere gli snapshot (versioni archiviate)
    di una determinata pagina web per un dato anno. Gestisce vari tipi di errore, inclusi errori di rete e timeout.
    
    Parametri:
    - url (str): L'URL della pagina web da cui ottenere gli snapshot.
    - year (int): L'anno per cui si desidera ottenere gli snapshot.
    
    Ritorna:
    - Una lista di URL degli snapshot ottenuti.
    """
    
    # Crea l'URL base per la richiesta API della Wayback Machine per un dato URL e anno
    base_url = f"https://web.archive.org/cdx/search/cdx?url={url}&from={year}&to={year}&output=json"
    
    # Usa la variabile globale use_proxy per determinare se utilizzare il proxy
    global use_proxy
    attempts = 0  # Inizializza il contatore dei tentativi a 0
    
    while True:  # Ciclo infinito che tenterà di fare la richiesta finché non avviene con successo
        try:
            # Stampa l'IP attuale, se si sta utilizzando il proxy
            if use_proxy:
                print(f"🌐 IP attuale (con proxy): {get_ip()} - Richiesta per {year}")
                response = requests.get(base_url, proxies=PROXIES, timeout=20)  # Esegui la richiesta con il proxy
            else:
                print(f"🚀 Tentativo senza proxy per {year}")
                response = requests.get(base_url, timeout=20)  # Esegui la richiesta senza il proxy
            
            response.raise_for_status()  # Solleva un'eccezione se la risposta HTTP non è di successo (status code != 200)
            
            data = response.json()  # Converte la risposta JSON in un oggetto Python
            
            # Restituisce una lista di URL degli snapshot, escludendo l'intestazione (primo elemento)
            #["urlkey","timestamp","original","mimetype","statuscode","digest","length"]
            return [f"https://web.archive.org/web/{entry[1]}/{entry[2]}" for entry in data[1:]]
        
        except requests.exceptions.HTTPError as e:  # Gestisce errori HTTP specifici
            if response.status_code == 429:  # Se l'errore è 429 (Too Many Requests), cambia IP
                print("⚠️ Errore 429: Cambio IP e riprovo...")
                if use_proxy:  # Se il proxy è attivo, cambia l'IP tramite Tor
                    change_ip()
            else:
                print(f"❌ Errore HTTP {response.status_code} per {year}: {e}")
                return []  # Se si verifica un altro errore HTTP, ritorna una lista vuota
        
        except requests.exceptions.ReadTimeout:  # Gestisce i timeout
            attempts += 1  # Incrementa il contatore dei tentativi
            print(f"Timeout nella richiesta ci ha messo troppo tempo, tentativo {attempts}")
            if attempts < 2:  # Se ci sono stati meno di 2 tentativi, cambia IP (se si usa il proxy)
                if use_proxy:
                    change_ip()
                
            else:
                return []  # Se il timeout persiste più di due volte, esce dalla funzione
        
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectionError, urllib3.exceptions.NewConnectionError) as e:
            # Gestisce errori di connessione, proxy non raggiungibile, ecc.
            if use_proxy:
                print(f"❌ Errore di connessione SOCKS5 ({type(e).__name__}): {e}. Disattivo proxy e riprovo senza Tor...")
                use_proxy = False  # Disattiva il proxy (Tor) e tenta la richiesta senza
            else:
                print(f"❌ Errore anche senza proxy: {e}")
                return []  # Se l'errore persiste anche senza proxy, esce dalla funzione
        
        except requests.exceptions.RequestException as e:
            # Gestisce qualsiasi altro tipo di errore generale nella richiesta
            print(f"❌ Errore nella richiesta per {year}: {e}")
            return []  # Se c'è un errore generico, ritorna una lista vuota
