import requests
import time
from datetime import datetime

# ══════════════════════════════════════
# Настройки
# ══════════════════════════════════════
TELEGRAM_TOKEN    = "7456674909:AAHOzkE4saghYV1qdwSx-GoKFnA-psM74nE"
TELEGRAM_CHAT_ID  = "@Profit_XAUUSD_WinRate85"
TWELVEDATA_KEY    = "a6b7b79510d24bb194dbf6f35efaa4d6"
CHECK_INTERVAL    = 120   # каждые 2 минуты = 720 запросов/день (лимит 800)
ALERT_COOLDOWN    = 900   # повтор алерта раз в 15 минут

# ══════════════════════════════════════
# Уровни
# ══════════════════════════════════════
LEVELS = [
    {"price": 4481.50, "name": "МАКС Д / Strong High",  "emoji": "🟡"},
    {"price": 4463.53, "name": "Зона 4H сопротивление", "emoji": "🟢"},
    {"price": 4431.98, "name": "4H и боковик M15",      "emoji": "🟡"},
    {"price": 4399.53, "name": "ATR",                    "emoji": "🔵"},
    {"price": 4381.83, "name": "4H поддержка",           "emoji": "🔵"},
    {"price": 4359.95, "name": "1H поддержка",           "emoji": "🟣"},
    {"price": 4335.78, "name": "30M зона",               "emoji": "🔵"},
    {"price": 4311.85, "name": "МИН Д / Weak Low",      "emoji": "🟢"},
    {"price": 4280.82, "name": "1H поддержка",           "emoji": "🟣"},
    {"price": 4252.04, "name": "4H поддержка",           "emoji": "🔵"},
    {"price": 4213.64, "name": "4H поддержка",           "emoji": "🔵"},
    {"price": 4180.71, "name": "4H поддержка",           "emoji": "🔵"},
    {"price": 4146.47, "name": "4H поддержка",           "emoji": "🔵"},
    {"price": 4110.90, "name": "4H поддержка",           "emoji": "🔵"},
    {"price": 4074.02, "name": "4H поддержка",           "emoji": "🔵"},
    {"price": 4042.41, "name": "4H поддержка",           "emoji": "🔵"},
    {"price": 4006.85, "name": "4H поддержка",           "emoji": "🔵"},
]

TOLERANCE = 0.80  # ±0.80 пунктов

# ══════════════════════════════════════
# Состояние алертов
# ══════════════════════════════════════
last_alerted = {lvl["price"]: 0 for lvl in LEVELS}


def get_gold_price():
    """Получаем цену через Twelve Data — реальное время"""
    try:
        url = f"https://api.twelvedata.com/price?symbol=XAU/USD&apikey={TWELVEDATA_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()
        if "price" in data:
            price = float(data["price"])
            if price > 3000:
                return price
        print(f"  Twelve Data ответ: {data}")
    except Exception as e:
        print(f"  Twelve Data fail: {e}")

    # Резервный источник — Yahoo Finance
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/XAUUSD=X"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        price = float(data["chart"]["result"][0]["meta"]["regularMarketPrice"])
        if price > 3000:
            print(f"  [резерв: yahoo] {price:.2f}")
            return price
    except Exception as e:
        print(f"  Yahoo fail: {e}")

    return None


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Ошибка Telegram: {e}")
        return False


def send_test_message(price):
    price_str = f"{price:.2f}" if price else "недоступна"
    msg = (
        "✅ <b>БОТ ЗАПУЩЕН НА ОБЛАКЕ!</b>\n\n"
        "☁️ Сервер: Railway (24/7)\n"
        "📡 Источник цены: Twelve Data\n"
        "📊 Инструмент: XAU/USD\n"
        f"💰 Текущая цена: <b>{price_str}</b>\n"
        f"⏱ Проверка каждые 2 минуты\n"
        f"🔕 Повтор алерта: раз в 15 мин\n"
        f"📐 Допуск касания: ±{TOLERANCE} пунктов\n\n"
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
    print("   XAU/USD ALERT BOT (ОБЛАКО)")
    print("=" * 40)
    print(f"📢 Канал: {TELEGRAM_CHAT_ID}")
    print(f"📋 Уровней: {len(LEVELS)}")
    print(f"⏱  Проверка: каждые 2 минуты")
    print(f"🔕 Повтор: раз в 15 мин")
    print(f"📐 Допуск: ±{TOLERANCE} пунктов")
    print("─" * 40)

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
