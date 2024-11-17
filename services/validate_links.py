import re


async def check_is_links_valid(links, pattern):
    """ проверка ссылок на валидность """
    valid_links = []
    non_valid_links = []

    for link in links:
        if re.match(pattern, link) is not None:
            valid_links.append(link)
        else:
            non_valid_links.append(link)

    if not non_valid_links:
        return True, valid_links

    # Иначе вернуть HTML
    html = "Замечены <strong>НЕ ВАЛИДНЫЕ</strong> ссылки:\n"
    for link in links:
        if link in valid_links:
            html += f"• {link}: ✅ Валидная\n\n"
        else:
            html += f"• {link}: ❌ Не валидная\n\n"
    return False, html
