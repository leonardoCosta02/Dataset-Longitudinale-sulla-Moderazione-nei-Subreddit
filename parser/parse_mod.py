from bs4 import BeautifulSoup
from scraper.logger_setup import setup_logger
logger = setup_logger("parser_logger", to_file=True, log_dir="parser/logger")

def  extract_moderators(html):
    soup = BeautifulSoup(html, 'html.parser')
    moderators = []

    # 1. Layout moderno (div[data-testid="moderator"])
    moderator_divs = soup.select('div[data-testid="moderator"]')
    if moderator_divs:
        logger.info("Layout rilevato: MODERNO")
        for mod in moderator_divs:
            name_tag = mod.select_one('a[href*="/user/"]')
            karma_tag = mod.find('span', string=lambda s: s and s.strip().isdigit())
            time_tag = mod.find('time')

            username = name_tag.text.strip() if name_tag else None
            karma = int(karma_tag.text.strip()) if karma_tag else None
            timestamp = time_tag['datetime'] if time_tag and time_tag.has_attr('datetime') else None

            if username:
                moderators.append({
                    'username': username,
                    'karma': karma,
                    'timestamp': timestamp
                })
                # Stampa delle informazioni per il layout moderno
                logger.info(f"Moderatore trovato (MODERNO): {username} - Karma: {karma}, Timestamp: {timestamp}")
        return moderators

    # 2. Layout con <div id="moderator-table"> (reddit vecchio)
    mod_table_div = soup.find('div', id='moderator-table')
    if mod_table_div:
        logger.info("Layout rilevato: VECCHIO (moderator-table)")
        rows = mod_table_div.select('table tr')
        for row in rows:
            a_tag = row.find('a', href=True)
            b_tag = row.find('b')

            username = a_tag.text.strip() if a_tag else None
            karma = int(b_tag.text.strip()) if b_tag and b_tag.text.strip().isdigit() else None

            if username:
                moderators.append({
                    'username': username,
                    'karma': karma,
                    'timestamp': None
                })
                # Stampa delle informazioni per il layout vecchio
                logger.info(f"Moderatore trovato (VECCHIO): {username} - Karma: {karma}")
        return moderators

    # 3. Layout con <div class="moderator-table">
    moderator_table_div = soup.find('div', class_='moderator-table')
    if moderator_table_div:
        logger.info("Layout rilevato: MODERATOR-TABLE")

        table = moderator_table_div.find('table')
        if not table:
            logger.warning("Tabella non trovata dentro 'moderator-table'")
            return moderators

        rows = table.find_all('tr')
        for row in rows:
            username = None
            karma = None
            permission = None
            timestamp = None

            a_tag = row.find('a', href=True)
            if a_tag:
                username = a_tag.get_text(strip=True)

            b_tag = row.find('b')
            if b_tag:
                try:
                    karma = int(b_tag.get_text(strip=True))
                except ValueError:
                    logger.debug(f"Karma non numerico per {username}: '{b_tag.get_text(strip=True)}'")

            # 1. Primo tentativo: cerca il tag .gray
            permission_tag = row.find('span', class_='gray')
            if permission_tag:
                permission = permission_tag.get_text(strip=True)

            # 2. Secondo tentativo: raccogli da permission-summary direttamente
            if not permission:
                #logger.info(f"Nessun span.gray per {username}, cerco span.permission-bit")
                summary_div = row.select_one('.permission-summary')
                if summary_div:
                    permission_bits = summary_div.select('span.permission-bit')
                    if permission_bits:
                        permission = ', '.join(bit.text.strip() for bit in permission_bits)

            # 3. Terzo tentativo: permission-summary annidato dentro permissions
            if not permission:
                #logger.info(f"Nessun span.permission-bit per {username}, cerco div.permissions dentro i <td>")
                for td in row.find_all('td'):
                    permissions_div = td.find('div', class_='permissions')
                    if permissions_div:
                        permission_bits = permissions_div.select('div.permission-summary span.permission-bit')
                        if permission_bits:
                            permission = ', '.join(bit.get_text(strip=True) for bit in permission_bits)
                            #logger.info(f"✅ Permessi estratti da div.permission-summary: {permission}")
                            break
                        #else:
                            #logger.debug(f"Nessun permission-bit visibile in permission-summary per {username}")

            # 4. Nuovo tentativo: prendi il contenuto di input[name="permissions"]
            if not permission:
                #logger.info(f"Nessun permission-summary per {username}, cerco input[name='permissions']")
                permissions_input = row.find('input', {'name': 'permissions'})
                if permissions_input:
                    permission = permissions_input.get('value', '').strip()
                    #logger.info(f"✅ Permessi estratti da input[name='permissions']: {permission}")
                #else:
                    #logger.warning(f"⚠️ Nessun input[name='permissions'] trovato per {username}")

            # Estrai testo da <time>
            time_tag = row.find('time')
            if time_tag:
                timestamp = time_tag.get_text(strip=True)

            if username:
                moderators.append({
                    'username': username,
                    'karma': karma,
                    'permission': permission,
                    'timestamp': timestamp
                })
                logger.info(
                    f"Moderatore trovato (MODERATOR-TABLE): {username} - "
                    f"Karma: {karma}, Permessi: {permission}, Time: {timestamp}"
                )

        return moderators




    # 4. Layout testuale (div.md con username (karma))
    md_div = soup.find('div', class_='md')
    if md_div:
        logger.info("Layout rilevato: TESTUALE (div.md)")
        lines = md_div.get_text(separator="\n").splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if '(' in line and ')' in line:
                try:
                    name_part, karma_part = line.split('(')
                    username = name_part.strip()
                    karma = int(karma_part.strip(') '))
                    moderators.append({
                        'username': username,
                        'karma': karma,
                        'timestamp': None
                    })
                    # Stampa delle informazioni per il layout testuale
                    logger.info(f"Moderatore trovato (TESTUALE): {username} - Karma: {karma}")
                except ValueError:
                    continue
        return moderators

    # 5. Nuovo layout con div.moderator-table
    moderator_table_div = soup.find('div', class_='moderator-table')
    if moderator_table_div:
        logger.info("Layout rilevato: MODERATOR-TABLE")
        rows = moderator_table_div.select('table tr')
        for row in rows:
            a_tag = row.find('a', href=True)
            b_tag = row.find('b')
            time_tag = row.find('time')

            username = a_tag.text.strip() if a_tag else None
            karma = int(b_tag.text.strip()) if b_tag and b_tag.text.strip().isdigit() else None
            timestamp = time_tag['datetime'] if time_tag and time_tag.has_attr('datetime') else None

            if username:
                moderators.append({
                    'username': username,
                    'karma': karma,
                    'timestamp': timestamp
                })
                # Stampa delle informazioni per il layout moderator-table
                logger.info(f"Moderatore trovato (MODERATOR-TABLE): {username} - Karma: {karma}, Timestamp: {timestamp}")
        return moderators
        

    logger.warning("Nessun layout riconosciuto")
    return []
