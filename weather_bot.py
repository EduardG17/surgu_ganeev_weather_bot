import telebot
import requests
from datetime import datetime

# --- Настройки ---
BOT_TOKEN = '9074258406:AAG5SkFn7McfA9wSK9KIeklp-3A2pXbRw_A'
bot = telebot.TeleBot(BOT_TOKEN)

# --- Функция для получения погоды ---
def get_weather(city):
    # 1. Геокодинг — официальный Open-Meteo
    geo_url = (
        f"https://geocoding-api.open-meteo.com/v1/search"
        f"?name={city}&count=1&language=ru&format=json"
    )
    try:
        geo_resp = requests.get(geo_url, timeout=15)
        geo_data = geo_resp.json()
        if not geo_data.get('results'):
            return f"❌ Город «{city}» не найден. Попробуйте написать по-другому."

        location = geo_data['results'][0]
        lat, lon = location['latitude'], location['longitude']
        city_name = location['name']
    except Exception as e:
        return f"⚠️ Ошибка при поиске города: {e}"

        # 2. Прогноз — официальный Open-Meteo
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code"
        f"&timezone=auto&forecast_days=7"
    )
    try:
        weather_resp = requests.get(weather_url, timeout=15)
        weather_data = weather_resp.json()
    except Exception as e:
        return f"⚠️ Ошибка при получении погоды: {e}"

    # Если сервер вернул не то, что ожидали — покажем, чтобы было видно
    if 'daily' not in weather_data:
        return f"⚠️ Неожиданный ответ от weather.tk.gg:\n{weather_data}"

    # 3. Формируем ответ
    daily = weather_data['daily']
    weather_desc = {
        0: "Ясно ☀️", 1: "Преим. ясно 🌤️", 2: "Переменная облачность ⛅", 3: "Пасмурно ☁️",
        45: "Туман 🌫️", 48: "Изморозь 🌫️",
        51: "Морось 🌦️", 53: "Морось 🌦️", 55: "Морось 🌦️",
        61: "Дождь 🌧️", 63: "Дождь 🌧️", 65: "Сильный дождь 🌧️",
        71: "Снег 🌨️", 73: "Снег 🌨️", 75: "Сильный снег 🌨️",
        80: "Ливень 🌦️", 81: "Ливень 🌦️", 82: "Сильный ливень ⛈️",
        95: "Гроза ⛈️", 96: "Гроза с градом ⛈️",
    }

    response_text = f"🗓 **Погода в {city_name} на 7 дней:**\n\n"
    for i in range(7):
        date_obj = datetime.strptime(daily['time'][i], '%Y-%m-%d')
        date_str = date_obj.strftime('%d.%m')
        t_max = daily['temperature_2m_max'][i]
        t_min = daily['temperature_2m_min'][i]
        rain = daily['precipitation_sum'][i]
        code = daily['weather_code'][i]
        desc = weather_desc.get(code, f"Код {code}")

        rain_info = f" | 💧 {rain} мм" if rain > 0 else ""
        response_text += f"**{date_str}**: {desc}, {t_min:.0f}...{t_max:.0f}°C{rain_info}\n"

    return response_text

# --- /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! 👋 Напиши мне название города, и я пришлю прогноз погоды на неделю.")

# --- Любой текст = город ---
@bot.message_handler(content_types=['text'])
def handle_city(message):
    city = message.text.strip()
    bot.send_chat_action(message.chat.id, 'typing')
    forecast = get_weather(city)
    bot.reply_to(message, forecast, parse_mode='Markdown')

# --- Запуск ---
if __name__ == '__main__':
    print("Бот запущен и ждет сообщений...")
    bot.infinity_polling(timeout=30, long_polling_timeout=20)