#!/usr/bin/env python3
"""
Робить watcher.py для Тбілісі з watcher.py бота Батумі (myhome_batumi, до 12.10.2026 — myhome-watcher).

Код Тбілісі — копія батумського; відрізняються лише рядки з таблиці REPLACEMENTS нижче:
назва міста, мова повідомлень у Telegram, фільтр «не сотрудничаю с риелторами», який є лише
в Тбілісі (сама перевірка — у no_realtors.py, таблиця лише підключає її), і друга група для
продажу (пошуки з «| sale» у searches.txt, як у боті ss.ge_tbilisi). У групі Тбілісі є
учасник, який не знає української, тож усе, що бот пише в групу, — російською. Журнал запусків і коментарі в
коді лишаються українськими, як у Батумі.

  python sync_from_batumi.py ../myhome_batumi/watcher.py

Скрипт перезаписує watcher.py поруч із собою. Якщо в батумському коді якийсь рядок
змінився і заміна не знайшлася (або знайшлася не стільки разів, скільки очікувалось), —
скрипт нічого не запише й скаже, який рядок: тоді поправити його в таблиці.
"""

import sys
from pathlib import Path

# (як у Батумі, як у Тбілісі, скільки разів трапляється в батумському watcher.py)
REPLACEMENTS = [
    # ── місто ──
    ("Оберіть на сайті Батумі, застосуйте",
     "Оберіть на сайті Тбілісі, застосуйте", 1),
    ("объявления об аренде квартиры в Батуми.",  # у Тбілісі ще будинки, комерція й продаж
     "объявления о недвижимости в Тбилиси.", 1),

    # ── повідомлення з оголошенням — російською ──
    ("or 'Нове оголошення'}",
     "or 'Новое объявление'}", 1),
    ("f\"кімнат: {clean(item['room'])}\"",
     "f\"комнат: {clean(item['room'])}\"", 1),
    ("f\"спалень: {clean(item['bedroom'])}\"",
     "f\"спален: {clean(item['bedroom'])}\"", 1),
    ("f\"поверх {clean(item['floor'])}\"",
     "f\"этаж {clean(item['floor'])}\"", 1),
    (", оновлено {updated:%d.%m %H:%M}",
     ", обновлено {updated:%d.%m %H:%M}", 1),
    ("(повністю — на сайті)",
     "(полностью — на сайте)", 1),
    ("\"⚠️ На myhome.ge автор позначений як агент\"",
     "\"⚠️ На myhome.ge автор отмечен как агент\"", 1),
    ("plural(site, \"оголошення\", \"оголошення\", \"оголошень\")",
     "plural(site, \"объявление\", \"объявления\", \"объявлений\")", 1),
    ("на myhome.ge — агент або інвестор\")",
     "на myhome.ge — агент или инвестор\")", 1),
    ("plural(count, \"оголошенні\", \"оголошеннях\", \"оголошеннях\")",
     "plural(count, \"объявлении\", \"объявлениях\", \"объявлениях\")", 1),
    ("f\"⚠️ Цей автор або телефон уже трапився в {count} {words} — агент або інвестор\"",
     "f\"⚠️ Этот автор или телефон уже встречался в {count} {words} — агент или инвестор\"", 1),
    ("\"⚠️ В описі згадується агенція або комісія\"",
     "\"⚠️ В описании упоминается агентство или комиссия\"", 1),
    ("\"✍️ Пише, що без посередників\"",
     "\"✍️ Пишет, что без посредников\"", 1),
    ("Відкрити на myhome.ge",  # посилання в повідомленні + заміна в print_listing
     "Открыть на myhome.ge", 2),

    # ── службові повідомлення в групу — російською ──
    ("\"✅ myhome.ge знову віддає дані, моніторинг працює.\"",
     "\"✅ myhome.ge снова отдаёт данные, мониторинг работает.\"", 1),
    ("\"⚠️ Кілька перевірок поспіль myhome.ge не віддає дані. Можливо, сайт змінив \"\n"
     "                  \"API або блокує запити — варто глянути лог запусків.\"",
     "\"⚠️ Несколько проверок подряд myhome.ge не отдаёт данные. Возможно, сайт изменил \"\n"
     "                  \"API или блокирует запросы — стоит посмотреть журнал запусков.\"", 1),
    ("f\"✅ Стежу за пошуком «{html.escape(label)}». Поточні {len(found)} \"\n"
     "                          \"оголошень запам'ятав — надсилатиму тільки нові.\"",
     "f\"✅ Слежу за поиском «{html.escape(label)}». Текущие {len(found)} \"\n"
     "                          \"объявлений запомнил — буду присылать только новые.\"", 1),
    ("\"✅ Бот підключено! Сюди приходитимуть нові оголошення від власників з myhome.ge.\"",
     "\"✅ Бот подключён! Сюда будут приходить новые объявления от собственников с myhome.ge.\"", 1),

    # ── лише Тбілісі: не надсилати, якщо автор пише «с агентствами не сотрудничаю» (no_realtors.py) ──
    ("from pathlib import Path\n",
     "from pathlib import Path\n"
     "\n"
     "import no_realtors  # лише Тбілісі (sync_from_batumi.py)\n", 1),
    ("MAX_ALERTS_PER_RUN = ",
     "SKIP_NO_REALTORS = True        # не надсилати, якщо автор пише «с агентствами не сотрудничаю»,\n"
     "                               # «агентам не звонить» (лише Тбілісі; «сотрудничаю 50%» — надсилати)\n"
     "MAX_ALERTS_PER_RUN = ", 1),
    # після перекладу: перевіряємо і грузинський оригінал, і російський переклад
    ("            if telegram_ready():\n"
     "                delivered = send_listing(item, label, count)\n",
     "            if SKIP_NO_REALTORS and no_realtors.refuses_realtors(\n"
     "                    plain_text(item.get(\"comment\")) + \" \" + str(item.get(\"_ru_comment\") or \"\")):\n"
     "                log(f\"  пропускаю {item['id']}: автор пише, що не співпрацює з рієлторами\")\n"
     "                delivered = True\n"
     "            elif telegram_ready():\n"
     "                delivered = send_listing(item, label, count)\n", 1),

    # ── лише Тбілісі: продаж — в окрему групу (як у ss.ge_tbilisi) ──
    # Пошук у searches.txt з третьою частиною «| sale» шле в чат TELEGRAM_CHAT_ID_SALE, решта —
    # в основну групу. Рядки нижче накладаються після попередніх (тексти вже російські).
    ("TELEGRAM_CHAT_ID = os.getenv(\"TELEGRAM_CHAT_ID\", \"\")  # кілька чатів — через кому\n",
     "TELEGRAM_CHAT_ID = os.getenv(\"TELEGRAM_CHAT_ID\", \"\")  # кілька чатів — через кому\n"
     "# Інші групи: пошук у searches.txt з третьою частиною «| sale» іде в чат з TELEGRAM_CHAT_ID_SALE\n"
     "# (у telegram.json — \"chat_id_sale\"). Без нього такий пошук пропускається, в основну групу не йде.\n", 1),
    ("    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, OPENAI_API_KEY\n",
     "    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, OPENAI_API_KEY, FILE_GROUP_CHATS\n", 1),
    ("    OPENAI_API_KEY = OPENAI_API_KEY or str(cfg.get(\"openai_key\") or \"\").strip()\n"
     "\n"
     "\n"
     "load_telegram_file()\n",
     "    OPENAI_API_KEY = OPENAI_API_KEY or str(cfg.get(\"openai_key\") or \"\").strip()\n"
     "    FILE_GROUP_CHATS = {k[len(\"chat_id_\"):].lower(): str(v or \"\").strip()\n"
     "                        for k, v in cfg.items() if k.startswith(\"chat_id_\")}\n"
     "\n"
     "\n"
     "FILE_GROUP_CHATS = {}  # chat_id інших груп з telegram.json: {\"sale\": \"-100…\"}\n"
     "load_telegram_file()\n", 1),
    ("        label, url = (\"\", line)\n"
     "        if \"|\" in line:\n"
     "            label, url = (part.strip() for part in line.split(\"|\", 1))\n"
     "        if \"myhome.ge\" not in url:\n"
     "            continue  # рядок-заглушка або щось стороннє\n"
     "        searches.append((label or \"myhome.ge\", url))\n",
     "        parts = [part.strip() for part in line.split(\"|\")]\n"
     "        if len(parts) == 1:  # лише посилання, без назви\n"
     "            parts.insert(0, \"\")\n"
     "        label, url, group = (parts + [\"\"])[:3]\n"
     "        if \"myhome.ge\" not in url:\n"
     "            continue  # рядок-заглушка або щось стороннє\n"
     "        if group and not re.fullmatch(r\"[A-Za-z0-9_]+\", group):\n"
     "            raise ConfigError(f\"назва групи «{group}» — лише латинські літери, цифри й _ (наприклад, sale)\")\n"
     "        searches.append((label or \"myhome.ge\", url, group.lower()))\n", 1),
    ("def chat_ids():\n"
     "    return [c.strip() for c in str(TELEGRAM_CHAT_ID).split(\",\") if c.strip()]\n"
     "\n"
     "\n"
     "def telegram_ready():\n"
     "    return bool(TELEGRAM_BOT_TOKEN and chat_ids())\n",
     "def chat_ids(group=\"\"):\n"
     "    \"\"\"Чати групи: основна — TELEGRAM_CHAT_ID, інша (sale) — TELEGRAM_CHAT_ID_SALE.\"\"\"\n"
     "    raw = (os.getenv(f\"TELEGRAM_CHAT_ID_{group.upper()}\") or FILE_GROUP_CHATS.get(group, \"\")\n"
     "           if group else TELEGRAM_CHAT_ID)\n"
     "    return [c.strip() for c in str(raw).split(\",\") if c.strip()]\n"
     "\n"
     "\n"
     "def telegram_ready(group=\"\"):\n"
     "    return bool(TELEGRAM_BOT_TOKEN and chat_ids(group))\n", 1),
    ("def send_text(text):\n"
     "    for chat in chat_ids():\n",
     "def send_text(text, group=\"\"):\n"
     "    for chat in chat_ids(group):\n", 1),
    ("def send_listing(item, label, count):\n"
     "    \"\"\"Надсилає оголошення у всі чати. True, якщо дійшло хоча б в один.\"\"\"\n",
     "def send_listing(item, label, count, group=\"\"):\n"
     "    \"\"\"Надсилає оголошення у всі чати групи. True, якщо дійшло хоча б в один.\"\"\"\n", 1),
    ("    delivered = False\n"
     "    for chat in chat_ids():\n",
     "    delivered = False\n"
     "    for chat in chat_ids(group):\n", 1),
    ("    for label, url in searches:\n",
     "    for label, url, group in searches:\n"
     "        if group and telegram_ready() and not telegram_ready(group):\n"
     "            log(f\"[{label}] не задано чат групи «{group}» (секрет TELEGRAM_CHAT_ID_{group.upper()}) — \"\n"
     "                \"пропускаю пошук\")\n"
     "            continue\n", 1),
    ("            if telegram_ready():\n"
     "                send_text(f\"✅ Слежу за поиском",
     "            if telegram_ready(group):\n"
     "                send_text(f\"✅ Слежу за поиском", 1),
    ("\"объявлений запомнил — буду присылать только новые.\")",
     "\"объявлений запомнил — буду присылать только новые.\", group)", 1),
    ("candidates.append((label, item))",
     "candidates.append((label, group, item))", 1),
    ("candidates.sort(key=lambda c: int(c[1][\"id\"]), reverse=True)",
     "candidates.sort(key=lambda c: int(c[2][\"id\"]), reverse=True)", 1),
    ("    for label, item in candidates:\n",
     "    for label, group, item in candidates:\n", 1),
    ("            elif telegram_ready():\n"
     "                delivered = send_listing(item, label, count)\n",
     "            elif telegram_ready(group):\n"
     "                delivered = send_listing(item, label, count, group)\n", 1),
    ("    label, url = load_searches()[0]\n"
     "    params = search_params(url)\n",
     "    label, url, group = load_searches()[0]\n"
     "    params = search_params(url)\n", 1),
    ("    if telegram_ready():\n"
     "        ok = send_listing(item, f\"🧪 ТЕСТ · {label}\", 0)\n",
     "    if telegram_ready(group):\n"
     "        ok = send_listing(item, f\"🧪 ТЕСТ · {label}\", 0, group)\n", 1),
    ("    label, url = load_searches()[0]\n"
     "    raw_list = ",
     "    label, url, _ = load_searches()[0]\n"
     "    raw_list = ", 1),
]


def convert(batumi_code):
    """Батумський код → тбіліський. Кидає ValueError, якщо якась заміна не підійшла."""
    code = batumi_code
    for old, new, expected in REPLACEMENTS:
        found = code.count(old)
        if found != expected:
            raise ValueError(f"очікував {expected}×, знайшов {found}×: {old!r}")
        code = code.replace(old, new)
    return code


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    source = Path(sys.argv[1])
    try:
        code = convert(source.read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"Не записав нічого. У батумському коді змінився рядок — поправте таблицю: {e}")
        return 1
    target = Path(__file__).resolve().parent / "watcher.py"
    target.write_text(code, encoding="utf-8")
    print(f"Готово: {target} (замін: {len(REPLACEMENTS)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
