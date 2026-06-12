import requests
import time
from datetime import datetime

# ══════════════════════════════════════
# Настройки
# ══════════════════════════════════════
TELEGRAM_TOKEN    = "7456674909:AAHOzkE4saghYV1qdwSx-GoKFnA-psM74nE"
TELEGRAM_CHAT_ID  = "@Profit_XAUUSD_WinRate85"
POLYGON_KEY       = "t36EhphV3LND4v2z8ispE2B2fa3lEe1t"
TWELVEDATA_KEY    = "a6b7b79510d24bb194dbf6f35efaa4d6"
CHECK_INTERVAL    = 60
ALERT_COOLDOWN    = 900

# ══════════════════════════════════════
# Уровни
# ══════════════════════════════════════
LEVELS = [
    {"price": 4405,56, "name": "4H поддержка",          "emoji": "🟣"},
    {"price": 4364,77, "name": "4H поддержка / боковик M15 ВВЕРХ", "emoji": "🟡"},
    {"price": 4328,62, "name": "4H поддержка",          "emoji": "🟣"},
    {"price": 4306,37, "name": "4H поддержка",          "emoji": "🟣"},
    {"price": 4282,73, "name": "4H поддержка / боковик M15 НИЗ", "emoji": "🟡"},
    {"price": 4253,53, "name": "4H поддержка",          "emoji": "🟣"},
    {"price": 4220,14, "name": "МАКС Д",          "emoji": "🔵"},
    {"price": 4194,20, "name": "4H поддержка",          "emoji": "🟣"},
    {"price": 4168,70, "name": "4H поддержка",          "emoji": "🟣"},
    {"price": 4145,53, "name": "4H поддержка",          "emoji": "🟣"},
    {"price": 4122,03, "name": "ATR поддержка / боковик M15 ВВЕРХ", "emoji": "🟡"},
    {"price": 4094.07, "name": "4H поддержка",          "emoji": "🟣"},
    {"price": 4074.83, "name": "4H поддержка",          "emoji": "🟣"},
    {"price": 4050.97, "name": "4H поддержка",          "emoji": "🟣"},
    {"price": 4023.92, "name": "МИН Д / боковик M15 НИЗ", "emoji": "🟡"},
    {"price": 3998,13, "name": "4H поддержка",          "emoji": "🟣"},
    {"price": 3976,80, "name": "4H поддержка",          "emoji": "🟣"},
    {"price": 3951,77, "name": "4H поддержка",          "emoji": "🟣"},
    {"price": 3930,45, "name": "4H поддержка",          "emoji": "🟣"},
    {"price": 3904,96, "name": "4H поддержка",          "emoji": "🟣"},
]

TOLERANCE = 1.50
last_alerted = {lvl["price"]: 0 for lvl in LEVELS}


def get_gold_price():
    """Получаем цену — Binance первый (универсальный), Polygon/TwelveData резерв"""

    # Источник 1: Binance XAUUSDT — открытый API, работает везде
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=XAUUSDT"
        r = requests.get(url, timeout=8)
        data = r.json()
        if "price" in data:
            price = float(data["price"])
            if price > 3000:
                print(f"  [binance] {price:.2f}", flush=True)
                return price
    except Exception as e:
        print(f"  binance fail: {e}", flush=True)

    # Источник 2: Polygon.io
    try:
        url = f"https://api.polygon.io/v2/last/trade/C:XAUUSD?apiKey={POLYGON_KEY}"
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get("status") == "OK" and "results" in data:
            price = float(data["results"]["p"])
            if price > 3000:
                print(f"  [polygon] {price:.2f}", flush=True)
                return price
    except Exception as e:
        print(f"  polygon fail: {e}", flush=True)

    # Источник 3: Twelve Data
    try:
        url = f"https://api.twelvedata.com/price?symbol=XAU/USD&apikey={TWELVEDATA_KEY}"
        r = requests.get(url, timeout=8)
        data = r.json()
        if "price" in data:
            price = float(data["price"])
            if price > 3000:
                print(f"  [twelvedata] {price:.2f}", flush=True)
                return price
    except Exception as e:
        print(f"  twelvedata fail: {e}", flush=True)

    print("  ❌ Все источники недоступны", flush=True)
    return None


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Ошибка Telegram: {e}", flush=True)
        return False


def send_test_message(price):
    price_str = f"{price:.2f}" if price else "недоступна"
    msg = (
        "✅ <b>БОТ ЗАПУЩЕН!</b>\n\n"
        "☁️ Сервер: Railway (24/7)\n"
        "📡 Источник цены: Binance / Polygon\n"
        "📊 Инструмент: XAU/USD\n"
        f"💰 Текущая цена: <b>{price_str}</b>\n"
        f"⏱ Проверка каждую минуту\n"
        f"🔕 Повтор алерта: раз в 15 мин\n"
        f"📐 Допуск: ±{TOLERANCE} пунктов\n\n"
        "<b>Слежу за уровнями:</b>\n"
        + "\n".join([f"{l['emoji']} <b>{l['price']}</b> — {l['name']}" for l in LEVELS])
        + "\n\n🟢 Мониторинг активен"
    )
    ok = send_telegram(msg)
    if ok:
        print("✅ Тестовое сообщение отправлено!", flush=True)
    else:
        print("❌ Ошибка отправки в Telegram", flush=True)


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
                if send_telegram(msg):
                    last_alerted[level_price] = now_ts
                    print(f"🔔 Алерт: {lvl['name']} @ {price:.2f}", flush=True)


def main():
    print("=" * 40, flush=True)
    print("   XAU/USD ALERT BOT (RAILWAY)", flush=True)
    print("=" * 40, flush=True)
    print(f"📢 Канал: {TELEGRAM_CHAT_ID}", flush=True)
    print(f"📋 Уровней: {len(LEVELS)}", flush=True)
    print(f"⏱  Проверка: каждую минуту", flush=True)
    print(f"🔕 Повтор: раз в 15 мин", flush=True)
    print(f"📐 Допуск: ±{TOLERANCE} пунктов", flush=True)
    print("─" * 40, flush=True)

    print("\n⏳ Получаю текущую цену...", flush=True)
    price = get_gold_price()
    if price:
        print(f"💰 Текущая цена: {price:.2f}", flush=True)
    send_test_message(price)

    print("─" * 40, flush=True)
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
