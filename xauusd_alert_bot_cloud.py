import requests
import time
from datetime import datetime

# ══════════════════════════════════════
# Справочник эмодзи — копируй нужный цвет
# ══════════════════════════════════════
# 🟢 зелёный
# 🔴 красный
# 🟡 жёлтый
# 🔵 синий
# 🟣 фиолетовый
# 🟠 оранжевый
# ⚪ белый
# ⚫ чёрный
# 🟤 коричневый

# ══════════════════════════════════════
# НАСТРОЙКИ
# ══════════════════════════════════════
TELEGRAM_TOKEN = "7456674909:AAHOzkE4saghYV1qdwSx-GoKFnA-psM74nE"
TELEGRAM_CHAT_ID = "@Profit_XAUUSD_WinRate85"
CHECK_INTERVAL = 60          # секунд
ALERT_COOLDOWN = 900         # секунд (15 мин)
TOLERANCE = 1.50             # пунктов

# ══════════════════════════════════════
# УРОВНИ
# ══════════════════════════════════════
LEVELS = [
     {"price": 4405.56, "name": "4H зона", "emoji": "🟣"},
     {"price": 4364.77, "name": "4H / боковик M15 верх", "emoji": "🟡"},
     {"price": 4328.62, "name": "4H зона", "emoji": "🟣"},
     {"price": 4306.37, "name": "4H зона", "emoji": "🟣"},
     {"price": 4282.73, "name": "4H / боковик M15 низ", "emoji": "🟡"},
     {"price": 4253.53, "name": "4H зона", "emoji": "🟣"},
     {"price": 4226.22, "name": "МАКС Д", "emoji": "🔴"},
     {"price": 4194.20, "name": "4H зона", "emoji": "🟣"},
     {"price": 4168.70, "name": "4H зона", "emoji": "🟣"},
     {"price": 4145.53, "name": "4H зона", "emoji": "🟣"},
     {"price": 4122.03, "name": "ATR / боковик M15 верх", "emoji": "🟡"},
     {"price": 4094.07, "name": "4H зона", "emoji": "🟣"},
     {"price": 4074.83, "name": "4H зона", "emoji": "🟣"},
     {"price": 4050.97, "name": "4H зона", "emoji": "🟣"},
     {"price": 4023.92, "name": "МИН Д / боковик M15 низ", "emoji": "🟡"},
     {"price": 3998.13, "name": "4H зона", "emoji": "🟣"},
     {"price": 3976.80, "name": "4H зона", "emoji": "🟣"},
     {"price": 3951.77, "name": "4H зона", "emoji": "🟣"},
     {"price": 3930.45, "name": "4H зона", "emoji": "🟣"},
     {"price": 3904.96, "name": "4H зона", "emoji": "🟣"},
    ]

last_alerted = {lvl["price"]: 0 for lvl in LEVELS}

def get_gold_price():
    """
    Получает спотовую цену XAU/USD.
    Приоритет:
      1. Swissquote (bid/ask mid, бесплатно, без ключа)
      2. Twelve Data (ваш ключ, резерв)
      3. Gold-API (публичный, без ключа)
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # 1. Swissquote — чистый спот XAU/USD
    try:
        url = "https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD"
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if data and len(data) > 0:
                profiles = data[0].get("spreadProfilePrices", [])
                if profiles:
                    bid = profiles[0].get("bid")
                    ask = profiles[0].get("ask")
                    if bid and ask:
                        price = float((bid + ask) / 2)   # mid-price
                        if price > 2000:
                            print(f"  [swissquote] {price:.2f}", flush=True)
                            return price
    except Exception as e:
        print(f"  [swissquote] Сбой: {e}", flush=True)

    # 2. Twelve Data (ваш API-ключ)
    try:
        url = "https://api.twelvedata.com/price?symbol=XAU/USD&apikey=a6b7b79510d24bb194dbf6f35efaa4d6"
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if "price" in data:
                price = float(data["price"])
                if price > 2000:
                    print(f"  [twelvedata] {price:.2f}", flush=True)
                    return price
    except Exception as e:
        print(f"  [twelvedata] Сбой: {e}", flush=True)

    # 3. Gold-API (публичный, без ключа)
    try:
        r = requests.get("https://api.gold-api.com/price/XAU/USD", headers=headers, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if "price" in data:
                price = float(data["price"])
                if price > 2000:
                    print(f"  [gold-api] {price:.2f}", flush=True)
                    return price
    except Exception as e:
        print(f"  [gold-api] Сбой: {e}", flush=True)

    print("  ❌ Все источники цены недоступны", flush=True)
    return None

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            return True
        else:
            print(f"❌ Telegram API ошибка {r.status_code}: {r.text}", flush=True)
            return False
    except Exception as e:
        print(f"❌ Сетевая ошибка Telegram: {e}", flush=True)
        return False

def send_test_message(price):
    price_str = f"{price:.2f}" if price else "недоступна"
    msg = (
        "✅ <b>БОТ ЗАПУЩЕН на СЕРВЕРЕ!</b>\n\n"
        "☁️ Сервер: Railway (24/7)\n"
        "📡 Источник: Swissquote (Спот XAU/USD) — как в TradingView\n"
        f"💰 Текущая цена: <b>{price_str}</b>\n"
        f"⏱ Проверка: каждую минуту\n"
        f"🔕 Повтор: раз в 15 мин\n"
        f"📐 Допуск: ±{TOLERANCE} пунктов\n\n"
        "<b>Слежу за уровнями:</b>\n"
        + "\n".join([f"{l['emoji']} <b>{l['price']}</b> — {l['name']}" for l in LEVELS])
        + "\n\n🟢 Мониторинг активен"
    )
    if send_telegram(msg):
        print("✅ Тестовое сообщение отправлено!", flush=True)
    else:
        print("❌ Ошибка отправки тестового сообщения", flush=True)

def check_levels(price):
    now_ts = time.time()
    for lvl in LEVELS:
        level_price = lvl["price"]
        diff = abs(price - level_price)

        if diff <= TOLERANCE:
            time_since = now_ts - last_alerted[level_price]
            if time_since >= ALERT_COOLDOWN:
                direction = "снизу ⬆️" if price < level_price else "сверху ⬇️"
                now_str = datetime.now().strftime("%H:%M:%S")
                msg = (
                    f"{lvl['emoji']} <b>XAU/USD достиг уровня!</b>\n\n"
                    f"📍 Уровень: <b>{lvl['name']}</b>\n"
                    f"💰 Цена уровня: <b>{level_price}</b>\n"
                    f"📊 Текущая цена: <b>{price:.2f}</b>\n"
                    f"📐 Подход: {direction}\n"
                    f"🕐 Время: {now_str}"
                )

                print(f"📤 Попытка отправки: {lvl['name']} @ {price:.2f}", flush=True)

                if send_telegram(msg):
                    last_alerted[level_price] = now_ts
                    print(f"✅ Алерт отправлен: {lvl['name']}", flush=True)
                else:
                    print(f"⚠️ Сбой отправки (см. ошибку выше)", flush=True)

def main():
    print("=" * 45, flush=True)
    print("   XAU/USD ALERT BOT (RAILWAY)", flush=True)
    print("=" * 45, flush=True)
    print(f"📢 Канал: {TELEGRAM_CHAT_ID}", flush=True)
    print(f"📋 Уровней: {len(LEVELS)}", flush=True)
    print("─" * 45, flush=True)

    print("\n⏳ Получаю текущую цену...", flush=True)
    price = get_gold_price()
    if price:
        print(f"💰 Текущая цена: {price:.2f}", flush=True)
        send_test_message(price)
    else:
        print("❌ Не удалось получить цену при запуске", flush=True)

    print("─" * 45, flush=True)
    print("🚀 Мониторинг запущен...\n", flush=True)

    while True:
        price = get_gold_price()
        if price:
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] XAU/USD = {price:.2f}", flush=True)
            check_levels(price)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Цена недоступна", flush=True)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
