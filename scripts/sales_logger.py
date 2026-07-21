import os
import datetime
import gspread
import telebot
from google.oauth2.service_account import Credentials
import json
import base64

# โหลดค่าจาก Environment Variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SHEET_ID = os.getenv("GOOGLE_SHEETS_ID")

bot = telebot.TeleBot(BOT_TOKEN)


def get_yesterday_summary():
    """ดึงข้อมูลยอดขายของเมื่อวานจาก Google Sheets"""
    # 1. ตั้งค่าการเชื่อมต่อ Google Sheets ผ่าน Base64 Secret (สำหรับรันบน GitHub Actions)
    b64_creds = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_B64")

    if b64_creds:
        creds_json = base64.b64decode(b64_creds).decode('utf-8')
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(
            creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    else:
        # Fallback เผื่อคุณอยากเทสในเครื่อง (จะไปดึงจากไฟล์แทน)
        creds = Credentials.from_service_account_file(
            "credentials.json", scopes=["https://www.googleapis.com/auth/spreadsheets"])

    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1

    # 2. คำนวณยอดของเมื่อวาน
    all_values = sheet.get_all_values()
    yesterday = (datetime.date.today() -
                 datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    total_sales = 0
    items_sold = 0

    for row in all_values[1:]:  # ข้ามบรรทัด Header
        if len(row) >= 5 and row[0] == yesterday:
            try:
                total_sales += float(row[4])
                items_sold += float(row[2])
            except ValueError:
                pass

    return yesterday, total_sales, items_sold


def send_report():
    """ส่งสรุปยอดเข้า Telegram"""
    try:
        date_str, total, items = get_yesterday_summary()

        # จัดรูปแบบข้อความ
        message = f"🌅 **สรุปยอดขายเมื่อวาน ({date_str})**\n\n"
        message += f"📦 สินค้าขายไป: {items:,.0f} ชิ้น\n"
        message += f"💰 ยอดรวม: {total:,.2f} บาท\n\n"
        message += "MilkLab Agent พร้อมลุยสำหรับออเดอร์วันนี้นะครับ! ✌️"

        # สั่งส่งข้อความ
        bot.send_message(CHAT_ID, message, parse_mode="Markdown")
        print("✅ ส่งรายงานตอนเช้าสำเร็จ!")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")


if __name__ == "__main__":
    send_report()
