import requests
import time
from datetime import datetime

# ══════════════════════════════════════
# НАСТРОЙКИ
# ══════════════════════════════════════
TELEGRAM_TOKEN = "7456674909:AAHOzkE4saghYV1qdwSx-GoKFnA-psM74nE"
TELEGRAM_CHAT_ID = "@Profit_XAUUSD_WinRate85"
CHECK_INTERVAL = 60
ALERT_COOLDOWN = 900
TOLERANCE = 1.50

# ══════════════════════════════════════
# УРОВНИ
# ══════════════════════════════════════
LEVELS = [
    {"price": 4486.72, "name": "30M поддержка", "emoji": "🟣"},
    {"price": 4455.32, "name": "1H поддержка", "emoji": "🟣"},
    {"price": 4426.61, "name": "4H поддержка", "emoji": "🔵"},
    {"price": 4411.84, "name": "30M поддержка", "emoji": "🟣"},
    {"price": 4407.77, "name": "4H поддержка", "emoji": "🔵"},
    {"price": 4388.03, "name": "4H поддержка", "emoji": "🔵"},
    {"price": 4368.30, "name": "4H поддержка", "emoji": "🔵"},
    {"price": 4353.40, "name": "МАКС Д / боковик M15", "emoji": "🟡"},
    {"price": 4328.82, "name": "4H поддержка", "emoji": "🔵"},
    {"price": 4304.60, "name": "ATR", "emoji": "🔵"},
    {"price": 4288.45, "name": "4H поддержка", "emoji": "🔵"},
    {"price": 4268.55, "name": "МИН Д / боковик M15", "emoji": "🟡"},
    {"price": 4245.39, "name": "4H поддержка", "emoji": "🔵"},
    {"price": 4215.78, "name": "1H поддержка", "emoji": "🟣"},
    {"price": 4188.87, "name": "1H поддержка", "emoji": "🟣"},
]

last_alerted = {lvl["price"]: 0 for lvl in LEVELS}

def get_gold_price():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    # 1. Yahoo Finance (GC=F — фьючерс COMEX) — РЕАЛЬНАЯ ЦЕНА ЗОЛОТА
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1m&range=1d"
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if "chart" in data and "result" in data["chart"] and len(data["chart"]["result"]) > 0:
                meta = data["chart"]["result"][0]["meta"]
                if "regularMarketPrice" in meta:
                    price = float(meta["regularMarketPrice"])
                    if price > 3000:
                        print(f"  [yahoo GC=F] {price:.2f}", flush=True)
                        return price
    except Exception as e:
        print(f"  [yahoo] Сбой: {e}", flush=True)

    # 2. Twelve Data (резервный, но с задержкой на бесплатном тарифе)
    try:
        url = "https://api.twelvedata.com/price?symbol=XAU/USD&apikey=a6b7b79510d24bb194dbf6f35efaa4d6"
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if "price" in data:
                price = float(data["price"])
                if price > 3000:
                    print(f"  [twelvedata] {price:.2f} (может быть задержка!)", flush=True)
                    return price
    except Exception as e:
        print(f"  [twelvedata] Сбой: {e}", flush=True)

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
        "✅ <b>БОТ ЗАПУЩЕН!</b>\n\n"
        "☁️ Сервер: Railway (24/7)\n"
        "📡 Источник: Yahoo Finance (фьючерс GC=F)\n"
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
