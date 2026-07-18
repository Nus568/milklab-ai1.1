"""MilkLab Sales Logger (S2).

Usage:
    python sales_logger.py --menu "นมหมีฮอกไกโด" --qty 2 --price 65

Reads GOOGLE_SHEETS_CREDENTIALS and TELEGRAM_BOT_TOKEN (or LINE_CHANNEL_TOKEN) from env.
Appends row [timestamp, menu, qty, price, total] to a Google Sheet,
then sends a notification via Telegram or LINE bot.

นักศึกษาต้องเติม TODO ใน 4 จุดด้านล่างใน Session 2 Lab 1.3


"""
import argparse
import os
import sys
import json
import gspread
import requests
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

from dotenv import load_dotenv  # <--- 1. ต้องเพิ่มบรรทัดนี้เพื่อรู้จักคำสั่ง

load_dotenv()  # <--- 2. ย้ายมาวางตรงนี้ (ก่อนดึงค่า os.getenv)

# ดึงค่าจาก environment variables
SHEET_ID = os.getenv("GOOGLE_SHEETS_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def append_to_sheet(menu: str, qty: int, price: float) -> dict:
    """TODO 1: ใช้ gspread บันทึกข้อมูลลง Sheet"""
    if not SHEET_ID:
        raise RuntimeError("Missing GOOGLE_SHEETS_ID")

    # 1. อ่าน credentials และยืนยันตัวตน
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'credentials.json', scope)
    client = gspread.authorize(creds)

    # 2. เปิดไฟล์ Google Sheets และเลือก Sheet แรก
    sheet = client.open_by_key(SHEET_ID).sheet1

    # 3. เตรียมข้อมูล
    total = qty * price
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 4. บันทึกข้อมูลลงแถวใหม่
    row = [timestamp, menu, qty, price, total]
    sheet.append_row(row)

    # 5. คืนค่าผลลัพธ์เพื่อนำไปส่ง Telegram ต่อ
    return {
        "timestamp": timestamp,
        "menu": menu,
        "qty": qty,
        "price": price,
        "total": total
    }


def send_notification(message: str) -> str:
    """TODO 2: ส่งข้อความผ่าน Telegram Bot"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError("Missing Telegram Credentials")

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    response = requests.post(url, json=payload)

    if not response.ok:
        raise RuntimeError(f"Telegram API Error: {response.text}")

    return "telegram"


def main() -> int:
    parser = argparse.ArgumentParser(description="MilkLab Sales Logger")
    parser.add_argument("--menu", required=True, help="ชื่อเมนู")
    parser.add_argument("--qty", type=int, required=True, help="จำนวนขวด")
    parser.add_argument("--price", type=float,
                        required=True, help="ราคาต่อขวด")
    args = parser.parse_args()

    try:
        # TODO 3: เรียก append_to_sheet
        row = append_to_sheet(args.menu, args.qty, args.price)
        total = row["total"]
    except Exception as exc:
        print(f"[ERROR] บันทึก Sheet ล้มเหลว: {exc}", file=sys.stderr)
        return 1

    try:
        # TODO 4: เรียก send_notification
        provider = send_notification(
            f"บันทึก {args.menu} x{args.qty} = {total} บาท")
    except Exception as exc:
        print(
            f"[WARN] บันทึก Sheet สำเร็จแต่ส่งแจ้งเตือนล้มเหลว: {exc}", file=sys.stderr)
        return 0

    print(f"[OK] บันทึกและแจ้งเตือนผ่าน {provider} เรียบร้อย ยอด {total} บาท")
    return 0


if __name__ == "__main__":
    sys.exit(main())
