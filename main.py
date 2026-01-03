import os
import requests
import asyncio
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ===== ENV VARIABLES =====
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
CHANNEL_ID = "@stockmarket_important_news"

IMPORTANT_KEYWORDS = [
    'fed','interest rate','inflation','gdp','earnings','profit','loss',
    'merger','ipo','dividend','crude oil','gold','recession','nse',
    'bse','sensex','nifty','rbi','sebi'
]

sent_news_ids = set()

def translate_to_hindi(text):
    try:
        return GoogleTranslator(source='en', target='hi').translate(text[:4500])
    except:
        return text

def is_important_news(title, description):
    text = (title + description).lower()
    return any(k in text for k in IMPORTANT_KEYWORDS)

def fetch_stock_news():
    url = "https://api.marketaux.com/v1/news/all"
    params = {
        "api_token": NEWS_API_KEY,
        "language": "en",
        "limit": 50,
        "published_after": (datetime.now() - timedelta(hours=2)).isoformat()
    }
    r = requests.get(url, params=params, timeout=10)
    return r.json().get("data", []) if r.status_code == 200 else []

def format_message(article):
    title = article.get("title", "")
    desc = article.get("description", "")
    url = article.get("url", "")
    time = article.get("published_at", "")

    return (
        "🔴 महत्वपूर्ण शेयर बाज़ार समाचार\n\n"
        f"📰 {translate_to_hindi(title)}\n\n"
        f"📝 {translate_to_hindi(desc[:200])}\n\n"
        f"🕐 {time}\n\n"
        f"🔗 [पूरी खबर पढ़ें]({url})\n\n"
        f"─────────────\n"
        f"🇬🇧 {title}"
    )

async def send_news(app):
    print(f"🔍 Checking news {datetime.now()}")
    for a in fetch_stock_news():
        uid = a.get("uuid")
        if uid in sent_news_ids:
            continue
        if is_important_news(a.get("title",""), a.get("description","")):
            await app.bot.send_message(
                chat_id=CHANNEL_ID,
                text=format_message(a),
                parse_mode="Markdown"
            )
            sent_news_ids.add(uid)
            await asyncio.sleep(2)

async def periodic_task(app):
    while True:
        await send_news(app)
        await asyncio.sleep(900)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📢 Stock Market Important News Bot active!")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_task(app))
    app.run_polling()

if _name_ == "_main_":
    main()