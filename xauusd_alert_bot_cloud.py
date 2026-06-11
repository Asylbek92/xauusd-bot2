import requests
import time
import threading
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

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
    {"price": 4486.72, "name": "30M поддержка",         "emoji": "🟣"},
    {"price": 4455.32, "name": "1H поддержка",          "emoji": "🟣"},
    {"price": 4426.61, "name": "4H поддержка",          "emoji": "🔵"},
    {"price": 4411.84, "name": "30M поддержка",         "emoji": "🟣"},
    {"price": 4407.77, "name": "4H поддержка",          "emoji": "🔵"},
    {"price": 4388.03, "name": "4H поддержка",          "emoji": "🔵"},
    {"price": 4368.30, "name": "4H поддержка",          "emoji": "🔵"},
    {"price": 4353.40, "name": "МАКС Д / боковик M15", "emoji": "🟡"},
    {"price": 4328.82, "name": "4H поддержка",          "emoji": "🔵"},
    {"price": 4304.60, "name": "ATR",                   "emoji": "🔵"},
    {"price": 4288.45, "name": "4H поддержка",          "emoji": "🔵"},
    {"price": 4268.55, "name": "МИН Д / боковик M15",  "emoji": "🟡"},
    {"price": 4245.39, "name": "4H поддержка",          "emoji": "🔵"},
    {"price": 4215.78, "name": "1H поддержка",          "emoji": "🟣"},
    {"price": 4188.87, "name": "1H поддержка",          "emoji": "🟣"},
]

TOLERANCE = 1.50
last_alerted = {lvl["price"]: 0 for lvl in LEVELS}


# ══════════════════════════════════════
# Веб-сервер — Render требует открытый порт
# ══════════════════════════════════════
class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"XAU/USD Bot is running!")

    def log_message(self, format, *args):
        pass

def start_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), PingHandler)
    print(f"🌐 Веб-сервер запущен на порту {port}")
    server.serve_forever()


# ══════════════════════════════════════
# Цена
# ══════════════════════════════════════
def get_gold_price():
    # Polygon.io
    try:
        url = f"https://api.polygon.io/v2/last/trade/C:XAUUSD?apiKey={POLYGON_KEY}"
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get("status") == "OK" and "results" in data:
            price = float(data["results"]["p"])
            if price > 3000:
                print(f"  [polygon] {price:.2f}")
                return price
        url2 = f"https://api.polygon.io/v1/last_quote/currencies/XAU/USD?apiKey={POLYGON_KEY}"
        r2 = requests.get(url2, timeout=8)
        data2 = r2.json()
        if "last" in data2:
            price = float(data2["last"]["ask"] + data2["last"]["bid"]) / 2
            if price > 3000:
                print(f"  [polygon forex] {price:.2f}")
                return price
    except Exception as e:
        print(f"  polygon fail: {e}")

    # Twelve Data
    try:
        url = f"https://api.twelvedata.com/price?symbol=XAU/USD&apikey={TWELVEDATA_KEY}"
        r = requests.get(url, timeout=8)
        data = r.json()
        if "price" in data:
            price = float(data["price"])
            if price > 3000:
                print(f"  [twelvedata] {price:.2f}")
                return price
    except Exception as e:
        print(f"  twelvedata fail: {e}")

    # Yahoo Finance
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/XAUUSD=X"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=8)
        data = r.json()
        price = float(data["chart"]["result"][0]["meta"]["regularMarketPrice"])
        if price > 3000:
            print(f"  [yahoo] {price:.2f}")
            return price
    except Exception as e:
        print(f"  yahoo fail: {e}")

    print("  ❌ Все источники недоступны")
    return None


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Ошибка Telegram: {e}")
        return False


def send_test_message(price):
    price_str = f"{price:.2f}" if price else "недоступна"
    msg = (
        "✅ <b>БОТ ЗАПУЩЕН НА RENDER!</b>\n\n"
        "☁️ Сервер: Render (24/7)\n"
        "📡 Источник цены: Polygon.io\n"
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
        print("✅ Тестовое сообщение отправлено!")
    else:
        print("❌ Ошибка отправки в Telegram")


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
                    print(f"🔔 Алерт: {lvl['name']} @ {price:.2f}")


def main():
    print("=" * 40)
    print("   XAU/USD ALERT BOT (RENDER)")
    print("=" * 40)
    print(f"📢 Канал: {TELEGRAM_CHAT_ID}")
    print(f"📋 Уровней: {len(LEVELS)}")
    print(f"⏱  Проверка: каждую минуту")
    print(f"🔕 Повтор: раз в 15 мин")
    print(f"📐 Допуск: ±{TOLERANCE} пунктов")
    print("─" * 40)

    # Запускаем веб-сервер в фоновом потоке
    t = threading.Thread(target=start_web_server, daemon=True)
    t.start()
    time.sleep(1)  # даём серверу секунду запуститься

    print("\n⏳ Получаю текущую цену...")
    price = get_gold_price()
    if price:
        print(f"💰 Текущая цена: {price:.2f}")
    send_test_message(price)

    print("─" * 40)
    print("🚀 Мониторинг запущен...\n")

    while True:
        price = get_gold_price()
        if price:
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] XAU/USD = {price:.2f}")
            check_levels(price)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Цена недоступна")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
