import requests
import time
from datetime import datetime

# ══════════════════════════════════════
# Настройки
# ══════════════════════════════════════
TELEGRAM_TOKEN    = "7456674909:AAHOzkE4saghYV1qdwSx-GoKFnA-psM74nE"
TELEGRAM_CHAT_ID  = "@Profit_XAUUSD_WinRate85"
TWELVEDATA_KEY    = "a6b7b79510d24bb194dbf6f35efaa4d6"
CHECK_INTERVAL    = 60   # Проверка каждую минуту
ALERT_COOLDOWN    = 900  # Повтор алерта на тот же уровень через 15 мин
TOLERANCE         = 1.50

# ══════════════════════════════════════
# Уровни (ИСПРАВЛЕНО: все пробелы в ключах удалены)
# ══════════════════════════════════════
LEVELS = [
    {"price": 4486.72, "name": "30M поддержка",          "emoji": "🟣"},
    {"price": 4455.32, "name": "1H поддержка",           "emoji": "🟣"},
    {"price": 4426.61, "name": "4H поддержка",           "emoji": "🔵"},
    {"price": 4411.84, "name": "30M поддержка",          "emoji": "🟣"},
    {"price": 4407.77, "name": "4H поддержка",           "emoji": "🔵"},
    {"price": 4388.03, "name": "4H поддержка",           "emoji": "🔵"},
    {"price": 4368.30, "name": "4H поддержка",           "emoji": "🔵"},
    {"price": 4353.40, "name": "МАКС Д / боковик M15",   "emoji": "🟡"},
    {"price": 4328.82, "name": "4H поддержка",           "emoji": "🔵"},
    {"price": 4304.60, "name": "ATR",                    "emoji": "🔵"},
    {"price": 4288.45, "name": "4H поддержка",           "emoji": "🔵"},
    {"price": 4268.55, "name": "МИН Д / боковик M15",    "emoji": "🟡"},
    {"price": 4245.39, "name": "4H поддержка",           "emoji": "🔵"},
    {"price": 4215.78, "name": "1H поддержка",           "emoji": "🟣"},
    {"price": 4188.87, "name": "1H поддержка",           "emoji": "🟣"},
]

# Инициализация словаря для кулдауна (без пробелов в ключах!)
last_alerted = {lvl["price"]: 0 for lvl in LEVELS}

def get_gold_price():
    # 1. Binance (основной, без лимитов запросов)
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=XAUUSDT"
        r = requests.get(url, timeout=8)
        data = r.json()
        if "price" in data:
            # replace(',', '.') на случай, если API вернёт число с запятой
            price = float(str(data["price"]).replace(',', '.'))
            if price > 3000:
                print(f"  [binance] {price:.2f}", flush=True)
                return price
    except Exception as e:
        print(f"  binance fail: {e}", flush=True)
    
    # 2. Twelve Data (резервный)
    try:
        # ИСПРАВЛЕНО: убраны пробелы в URL
        url = f"https://api.twelvedata.com/price?symbol=XAU/USD&apikey={TWELVEDATA_KEY}"
        r = requests.get(url, timeout=8)
        data = r.json()
        if "price" in data:
            price = float(str(data["price"]).replace(',', '.'))
            if price > 3000:
                print(f"  [twelvedata] {price:.2f}", flush=True)
                return price
    except Exception as e:
        print(f"  twelvedata fail: {e}", flush=True)
        
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
            # ТЕПЕРЬ МЫ ВИДИМ ТОЧНУЮ ПРИЧИНУ, ПОЧЕМУ TELEGRAM ОТКЛОНИЛ СООБЩЕНИЕ
            print(f"❌ Ошибка Telegram API: {r.status_code} | {r.text}", flush=True)
            return False
    except Exception as e:
        print(f"❌ Сетевая ошибка Telegram: {e}", flush=True)
        return False

def send_test_message(price):
    price_str = f"{price:.2f}" if price else "недоступна"
    msg = (
        "✅ <b>БОТ ЗАПУЩЕН!</b>\n\n"
        "☁️ Сервер: Railway (24/7)\n"
        "📡 Источник: Binance + Twelve Data\n"
        f"💰 Текущая цена: <b>{price_str}</b>\n"
        f"⏱ Проверка: каждую минуту\n"
        f"🔕 Повтор алерта: раз в 15 мин\n"
        f"📐 Допуск: ±{TOLERANCE} пунктов\n\n"
        "<b>Слежу за уровнями:</b>\n"
        + "\n".join([f"{l['emoji']} <b>{l['price']}</b> — {l['name']}" for l in LEVELS])
        + "\n\n🟢 Мониторинг активен"
    )
    if send_telegram(msg):
        print("✅ Тестовое сообщение отправлено!", flush=True)
    else:
        print("❌ Ошибка отправки тестового сообщения (см. лог выше)", flush=True)

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
                
                # Логируем попытку отправки, чтобы вы видели, что бот сработал
                print(f"📤 Попытка отправки алерта: {lvl['name']} @ {price:.2f}", flush=True)
                
                if send_telegram(msg):
                    last_alerted[level_price] = now_ts
                    print(f"✅ Алерт успешно отправлен: {lvl['name']}", flush=True)
                else:
                    print(f"⚠️ Сбой отправки алерта (см. ошибку Telegram выше)", flush=True)

def main():
    print("=" * 45, flush=True)
    print("   XAU/USD ALERT BOT (RAILWAY)", flush=True)
    print("=" * 45, flush=True)
    print(f"📢 Канал: {TELEGRAM_CHAT_ID}", flush=True)
    print(f"📋 Уровней: {len(LEVELS)}", flush=True)
    print(f"⏱  Проверка: каждую минуту", flush=True)
    print(f"🔕 Повтор: раз в 15 мин", flush=True)
    print(f"📐 Допуск: ±{TOLERANCE} пунктов", flush=True)
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
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Цена недоступна, проверка пропущена", flush=True)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
