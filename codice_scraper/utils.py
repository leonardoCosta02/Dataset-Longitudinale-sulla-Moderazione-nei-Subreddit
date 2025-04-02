def extract_month(url):
    """
    Estrae il mese dall'URL di uno snapshot Wayback Machine.
    
    Parametri:
    url (str): L'URL dello snapshot.
    
    Ritorna:
    int | None: Il numero del mese (1-12) se estratto correttamente, altrimenti None.
    """
    try:
        # L'URL degli snapshot contiene la data nel formato AAAAMMGG (es. 20230415 per il 15 aprile 2023)
        return int(url.split("/")[4][4:6])  # Prende i caratteri 4-6 della data per ottenere il mese
    except (IndexError, ValueError):
        # Se la struttura dell'URL non è corretta o non può essere convertita in intero, ritorna None
        return None


def get_valid_snapshot(urls, start_month, end_month):
    """
    Trova il primo snapshot disponibile in un determinato intervallo di mesi.
    
    Parametri:
    urls (list): Lista di URL degli snapshot.
    start_month (int): Mese di inizio dell'intervallo (1-12).
    end_month (int): Mese di fine dell'intervallo (1-12).
    
    Ritorna:
    tuple | None: Una tupla contenente l'URL valido e il suo mese, oppure None se nessun snapshot è valido.
    """
    for url in urls:
        month = extract_month(url)  # Estrae il mese dall'URL
        if month and start_month <= month <= end_month:  # Controlla se è nell'intervallo desiderato
            return url, month  # Ritorna il primo URL valido con il suo mese
    
    return None  # Nessuno snapshot valido trovato


def save_html_page(url, html):
    """
    Salva il contenuto HTML di una pagina in un file locale.
    
    Parametri:
    url (str): L'URL della pagina salvata (utilizzato per il nome del file).
    html (str): Il contenuto HTML della pagina.
    
    Ritorna:
    str: Il percorso del file salvato.
    """
    # Crea un nome file sicuro sostituendo caratteri non consentiti nei nomi dei file
    filename = f"html_cache/{url.replace('/', '_').replace(':', '_')}.html"
    
    # Apre il file in modalità scrittura con codifica UTF-8 e scrive l'HTML
    with open(filename, "w", encoding="utf-8") as file:
        file.write(html)
    
    return filename  # Ritorna il percorso del file salvato
