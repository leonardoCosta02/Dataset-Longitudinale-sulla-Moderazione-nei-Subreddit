from bs4 import BeautifulSoup
from app.scraper.logger_setup import setup_logger
logger = setup_logger("parser_logger", to_file=True, log_dir="app/parser/logger")
def extract_moderators(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    moderators = []

    for row in soup.find_all('tr'):
        user_link = row.find('a')
        if user_link and '/user/' in user_link.get('href', ''):
            username = user_link.text.strip()

            # CASE 1: <span> with "permissions:"
            permissions_span = row.find('span', string=lambda s: s and 'permissions:' in s)
            if permissions_span:
                perms = permissions_span.text.strip().split('permissions:')[-1].strip()
                permissions = [p.strip() for p in perms.split(',')]

            else:
                # CASE 2: <li> right after username
                li_tag = row.find('li')
                if li_tag and 'permissions:' in li_tag.text:
                    perms = li_tag.text.strip().split('permissions:')[-1].strip()
                    permissions = [p.strip() for p in perms.split(',')]
                else:
                    # CASE 3: permissions in next <td>
                    tds = row.find_all('td')
                    permissions = []
                    for td in tds:
                        if td.find('a') == user_link:
                            next_td = td.find_next_sibling('td')
                            if next_td:
                                perms = next_td.text.strip()
                                if perms:
                                    permissions = [p.strip() for p in perms.split(',')]
                            break

            moderators.append({
                'username': username,
                'permissions': permissions
            })

            if not moderators:
                logger.warning("Nessun moderatore trovato.")
            else:
                for mod in moderators:
                    logger.info(f"Moderatore: {mod['username']}")
                    if mod['permissions']:
                            logger.info(f"Permessi: {', '.join(mod['permissions'])}")
                    else:
                        print("Permessi: (nessuno specificato)")
                        print("---")

    return moderators
