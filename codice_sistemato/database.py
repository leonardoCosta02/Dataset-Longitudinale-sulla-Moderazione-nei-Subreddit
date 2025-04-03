def insert_html_document(url, file_path, collection):
    """Inserisce nel database un documento con URL e percorso del file HTML.
    
    Questa funzione crea un documento che contiene l'URL e il percorso del file HTML 
    e lo inserisce nella collection di MongoDB passata come parametro. 
    In seguito, stampa una conferma del salvataggio.
    
    Parametri:
    - url (str): L'URL della pagina HTML che è stata scaricata.
    - file_path (str): Il percorso nel file system dove il file HTML è stato salvato.
    - collection (pymongo.collection.Collection): La collection di MongoDB dove il documento sarà inserito.
    
    Ritorna:
    - None
    """
    
    # Crea un dizionario che rappresenta il documento da inserire nel database
    document = {
        "html_url": url,  # Memorizza l'URL nel campo "html_url"
        "file_path": file_path  # Memorizza il percorso del file nel campo "file_path"
    }
    
    # Inserisce il documento creato nella collection di MongoDB
    collection.insert_one(document)
    
    # Stampa un messaggio di conferma che l'inserimento è avvenuto con successo
    print(f"Salvato in MongoDB: {url} -> {file_path}")
