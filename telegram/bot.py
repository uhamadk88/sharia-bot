import sqlite3
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os

# --- ١. ڕێکخستنی سێرڤەری وێب بۆ ئەوەی Render هەڵەی Port نەدات ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    # ڕێندەر پۆرتی تایبەت بەخۆی بەکاردەهێنێت، ئەگەر نەبوو پۆرتی 10000 دادەنێین
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- ٢. زانیارییەکانی بوت و مامۆستا ---
# دڵنیابە ئەم تۆکنە نوێیەیە کە لە BotFather وەرتگرتووە
BOT_TOKEN = '8760836499:AAHZMQ_8S-vt1QVo-fdR92vZt7vJJPBZ7BA'
TEACHER_ID = 733089564
bot = telebot.TeleBot(BOT_TOKEN)

# --- ٣. بەشی بنکەی زانیاری (Database) ---
def init_db():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (msg_id INTEGER PRIMARY KEY, user_id INTEGER)''')
    conn.commit()
    conn.close()

def save_message(msg_id, user_id):
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO messages VALUES (?, ?)", (msg_id, user_id))
    conn.commit()
    conn.close()

def get_user_id(msg_id):
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT user_id FROM messages WHERE msg_id=?", (msg_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# --- ٤. بەڕێوەبردنی فەرمانی /start ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.id == TEACHER_ID:
        bot.reply_to(message, "✅ **بەخێربێیت مامۆستا.**\n\nتۆ ئێستا لە پانێڵی بەڕێوەبردنی بوتەکەیت. بۆ وەڵامدانەوەی هەر پرسیارێک، تەنها 'Reply' لەسەر نامەکە بکە.", parse_mode="Markdown")
    else:
        welcome_text = (
            "🌹 **بەخێربێیت بۆ بوت وەڵامە شەرعییەکان**\n\n"
            "ئەم پلاتفۆرمە تەرخانکراوە بۆ وەڵامدانەوەی پرسیارە ئایینییەکانت بەپێی قورئان و سوننەت.\n\n"
            "**تێبینی گرنگ:**\n"
            "سیستەمی بوتەکە بە شێوەیەک داڕێژراوە کە **ناوی تۆ و ناسنامەکەت** بە هیچ شێوەیەک لای مامۆستا دەرناکەوێت. دەتوانیت بە تەواوی دڵنیایی و نهێنییەوە پرسیارەکانت ئاراستە بکەیت.\n\n"
            "📥 **تکایە پرسیارەکەت لێرە بنووسە...**"
        )
        bot.reply_to(message, welcome_text, parse_mode="Markdown")

# --- ٥. بەڕێوەبردنی نامە هاتوەکان ---
@bot.message_handler(content_types=['text', 'photo', 'voice', 'document', 'video'])
def handle_incoming_messages(message):
    try:
        # ئەگەر نامەکە لەلایەن مامۆستاوە بێت بۆ وەڵامدانەوە
        if message.chat.id == TEACHER_ID:
            if message.reply_to_message:
                target_user_id = get_user_id(message.reply_to_message.message_id)
                if target_user_id:
                    if message.content_type == 'text':
                        bot.send_message(target_user_id, f"📌 **وەڵامی مامۆستا بۆ پرسیارەکەت:**\n\n{message.text}", parse_mode="Markdown")
                    else:
                        bot.copy_message(target_user_id, message.chat.id, message.message_id)
                    bot.reply_to(message, "✅ وەڵامەکەت بۆ قوتابی نێردرا.")
                else:
                    bot.reply_to(message, "❌ زانیاری ئەم قوتابییە لە داتابەیس نەدۆزرایەوە.")
            else:
                bot.reply_to(message, "تکایە 'Reply' بەکاربهێنە بۆ وەڵامدانەوەی قوتابی.")
        
        # ئەگەر نامەکە لەلایەن قوتابییەوە بێت بۆ پرسیارکردن
        else:
            if message.content_type == 'text':
                sent_msg = bot.send_message(TEACHER_ID, f"❓ **پرسیارێکی نوێ گەیشت:**\n\n{message.text}")
            else:
                sent_msg = bot.copy_message(TEACHER_ID, message.chat.id, message.message_id, caption="❓ پرسیار (فایل/وێنە)")
            
            save_message(sent_msg.message_id, message.chat.id)
            
            confirmation_text = "✅ **پرسیارەکەت بە سەرکەوتوویی تۆمارکرا.**\n\nبەم زووانە لەلایەن مامۆستاوە پێداچوونەوەی بۆ دەکرێت."
            bot.reply_to(message, confirmation_text, parse_mode="Markdown")

    except Exception as e:
        print(f"Error handling message: {e}")

# --- ٦. دەستپێکردنی سێرڤەر و بوت ---
if __name__ == "__main__":
    init_db()
    
    # یەکەم جار سێرڤەری Flask هەڵدەگیرسێنین بۆ ئەوەی Render سوور نەبێتەوە
    keep_alive()
    print("Web server is running on port 10000...")

    # سڕینەوەی وێبهوکە کۆنەکان بۆ چارەسەری کێشەی Conflict
    try:
        bot.remove_webhook()
        bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print(f"Webhook error: {e}")

    print("Bot is starting polling...")
    # بەکارهێنانی infinity_polling بۆ ئەوەی بوتەکە نەکوژێتەوە
    bot.infinity_polling()
