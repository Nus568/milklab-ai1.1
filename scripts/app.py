# app.py
import os
import telebot
from dotenv import load_dotenv
from agent_harness import process_user_message

# โหลดค่าจากไฟล์ .env
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 สวัสดีครับ! MilkLab Agent พร้อมให้บริการ\nคุณสามารถสั่งให้ผม:\n- บันทึกยอดขาย (เช่น 'ขายกาแฟ 2 แก้ว แก้วละ 50')\n- ดูสรุปยอดขายวันนี้\n- เช็กราคาสินค้า")


@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # Guardrail 5: Authentication (จำกัดสิทธิ์เฉพาะคุณเท่านั้นที่ใช้บอทได้)
    if str(message.chat.id) != str(ALLOWED_CHAT_ID):
        bot.reply_to(message, "⛔ ขออภัย คุณไม่ได้รับสิทธิ์ให้ใช้งานบอทนี้ครับ")
        return

    # แสดงสถานะ "กำลังพิมพ์..." ให้ดูเป็นธรรมชาติ
    bot.send_chat_action(message.chat.id, 'typing')

    try:
        # ส่งข้อความเข้า Agent Harness
        reply_text = process_user_message(message.text)
        bot.reply_to(message, reply_text)
    except Exception as e:
        bot.reply_to(message, f"❌ ไม่สามารถดำเนินการได้: {e}")


if __name__ == "__main__":
    print("🚀 เริ่มรัน MilkLab Agent Bot ...")
    bot.infinity_polling()
