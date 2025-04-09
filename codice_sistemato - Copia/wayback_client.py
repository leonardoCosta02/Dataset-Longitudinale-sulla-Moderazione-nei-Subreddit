### Nuovo file: wayback_client.py
import time  # Modulo per la gestione del tempo (es. sleep, timestamp)
import random  # Per selezionare un user-agent casuale
import requests  # Per effettuare richieste HTTP
from functools import wraps  # Per mantenere i metadata originali della funzione decorata
from logger_setup import setup_logger  # Logger personalizzato del progetto

# Inizializza il logger per questo modulo
logger = setup_logger(__name__, to_file=True)

# Lista di user-agent da usare per "mascherare" le richieste e sembrare browser reali
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Pixel 4 XL Build/QP1A.190711.020) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
]

class ErrorType:
    SUCCESS = 0
    RETRYABLE_TIMEOUT = 1
    RETRYABLE_CONN_ERR = 2
    NON_RETRYABLE_HTTP_ERR = 3
    SSL_ERROR = 4
    GENERIC_ERROR = 5
    MAX_RETRIES_EXCEEDED = 6

# Decoratore per limitare la frequenza delle chiamate alla funzione decorata
# min_interval: tempo minimo in secondi da attendere tra due chiamate consecutive

def ratelimit(min_interval=4.0):  # Impostato per rispettare il limite di 15 richieste/minuto
    def decorator(func):
        last_call = [0.0]  # Memorizza il timestamp dell'ultima chiamata (usiamo lista per mutabilità)

        @wraps(func)  # Mantiene nome e docstring originali della funzione
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]  # Calcola quanto tempo è passato dall'ultima chiamata
            if elapsed < min_interval:
                wait_time = min_interval - elapsed  # Tempo da attendere prima di chiamare di nuovo
                logger.info(f"⏳ Rate limit attivo: attendo {wait_time:.2f}s")
                time.sleep(wait_time)  # Attende il tempo necessario per rispettare il rate limit
            last_call[0] = time.time()  # Aggiorna il timestamp della chiamata corrente
            return func(*args, **kwargs)  # Esegue la funzione originale

        return wrapper  # Ritorna il nuovo wrapper "rate-limited"
    return decorator

@ratelimit(min_interval=4.0)
def get_wayback(url, params, headers=None, timeout=20, max_retries=3, fallback_to_http=True, **kwargs):
    """
    Wrapper robusto per requests.get con gestione automatica degli errori di rete,
    fallback da HTTPS→HTTP, user-agent casuale, rate limiting e logging centralizzato.
    """
    attempts = 0
    headers = headers or {}
    user_agent = random.choice(user_agents)
    headers["User-Agent"] = user_agent

    # Aggiunge opzioni per limitare le dimensioni della risposta (es. API IA)
    if params is None:
        params = {}

    logger.info(f"Parametri di richiesta: {params}")
    original_url = url

    while attempts < max_retries:
        try:
            logger.info(f"🌐 GET {url} | User-Agent: {user_agent}")
            response = requests.get(url, params=params,headers=headers, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response,ErrorType.SUCCESS

        except requests.exceptions.SSLError as e:
            logger.warning(f"⚠️ Errore SSL (certificati non validi?): {e}")
            return None,ErrorType.SSL_ERROR

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                wait_time = int(retry_after) if retry_after and retry_after.isdigit() else 30
                logger.warning(f"🔁 429 Too Many Requests. Attesa di {wait_time}s")
                time.sleep(wait_time)
            elif response.status_code == 403 and fallback_to_http and url.startswith("https://"):
                logger.warning("🔁 403 Forbidden. Provo fallback a HTTP...")
                url = url.replace("https://", "http://")
                fallback_to_http = False  # evita loop infinito
            elif 500 <= response.status_code < 600:
                logger.warning(f"⚠️ Server error {response.status_code}. Ritento...")
                time.sleep(10)
            else:
                logger.error(f"❌ HTTP error {response.status_code} per {original_url}")
                return None,ErrorType.NON_RETRYABLE_HTTP_ERR

        except requests.exceptions.Timeout:
            logger.warning(f"⏳ Timeout per {original_url} (tentativo {attempts+1}/{max_retries})")
            time.sleep(5)

        except (requests.exceptions.ConnectionError, requests.exceptions.ProxyError) as e:
            logger.warning(f"🔌 Errore di connessione: {e}")
            time.sleep(10)
            return None, ErrorType.RETRYABLE_CONN_ERR

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Errore generico per {original_url}: {e}")
            return None,ErrorType.GENERIC_ERROR

        attempts += 1

    logger.error(f"❌ Fallimento dopo {max_retries} tentativi per {original_url}")
    return None,ErrorType.MAX_RETRIES_EXCEEDED
