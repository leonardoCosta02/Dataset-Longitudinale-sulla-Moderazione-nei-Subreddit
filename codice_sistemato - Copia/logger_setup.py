import logging
import os

def setup_logger(name, to_file=False, level=logging.INFO, log_dir="logs"):
    """
    Crea e restituisce un logger con un nome specifico.
    
    Parametri:
    - name (str): nome del logger, tipicamente __name__ del modulo.
    - to_file (bool): se True, salva i log anche su file.
    - level (int): livello di logging (es. logging.INFO, logging.DEBUG).
    - log_dir (str): directory in cui salvare i log se to_file=True.

    Ritorna:
    - logging.Logger: un'istanza configurata di logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Evita di aggiungere handler multipli se è già configurato
    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler opzionale
    if to_file:
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"{name}.log")
        file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
