import os
import datetime
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# โหลดค่าตัวแปรจาก .env
load_dotenv()

# ตั้งค่าการเชื่อมต่อ Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
# เรียกใช้ credentials.json ที่คุณมีใน Workspace
creds = Credentials.from_service_account_file(
    "credentials.json", scopes=SCOPES)
client = gspread.authorize(creds)

SHEET_ID = os.getenv("GOOGLE_SHEETS_ID")

# --- Tool 1: บันทึกยอดขาย (ลง Google Sheets) ---


def log_sales(product_name: str, quantity: int, price_per_unit: float) -> str:
    """ใช้บันทึกยอดขายสินค้าลงระบบ"""
    if quantity <= 0 or price_per_unit < 0:
        return "❌ การบันทึกถูกระงับ: จำนวนสินค้าหรือราคาไม่สามารถติดลบได้"

    total = quantity * price_per_unit
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    try:
        # เปิดชีตหน้าแรก (sheet1)
        sheet = client.open_by_key(SHEET_ID).sheet1
        # บันทึกลงแถวใหม่: [วันที่, ชื่อสินค้า, จำนวน, ราคาต่อหน่วย, ยอดรวม]
        sheet.append_row(
            [today_str, product_name, quantity, price_per_unit, total])
        return f"✅ บันทึกยอดขายสำเร็จ: {product_name} จำนวน {quantity} ชิ้น (ยอดรวม {total} บาท)"
    except Exception as e:
        return f"⚠️ เกิดข้อผิดพลาดในการบันทึกลงชีต: {e}"

# --- Tool 2: สรุปยอดขายประจำวัน (อ่านจาก Google Sheets) ---


def get_daily_summary() -> str:
    """ใช้ขอดูสรุปยอดขายรวมเฉพาะของวันนี้"""
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    try:
        sheet = client.open_by_key(SHEET_ID).sheet1
        all_values = sheet.get_all_values()  # ดึงข้อมูลทั้งหมดมาเป็น List

        daily_total = 0
        # ข้ามแถวแรกที่เป็น Header (เริ่มจาก index 1)
        for row in all_values[1:]:
            # เช็คว่าแถวมีข้อมูลครบและวันที่ตรงกับวันนี้ (สมมติว่าวันที่อยู่คอลัมน์แรก index 0 และยอดรวมอยู่คอลัมน์ที่ 5 index 4)
            if len(row) >= 5 and row[0] == today_str:
                try:
                    daily_total += float(row[4])
                except ValueError:
                    pass  # ข้ามกรณีที่ข้อมูลไม่ใช่ตัวเลข

        return f"📊 สรุปยอดขายวันที่ {today_str}: ยอดรวมทั้งหมด {daily_total} บาท"
    except Exception as e:
        return f"⚠️ ไม่สามารถดึงข้อมูลสรุปได้: {e}"

# --- Tool 3: เช็กข้อมูล/ราคาสินค้า ---


def check_product_info(product_name: str) -> str:
    """ใช้ตรวจสอบราคาของสินค้าในร้าน"""
    mock_db = {"กาแฟ": 50, "นม": 45, "เค้ก": 80}
    if product_name not in mock_db:
        return f"❓ ไม่พบข้อมูลของ '{product_name}' ในระบบครับ"
    return f"ℹ️ สินค้า: {product_name} ราคา {mock_db[product_name]} บาท"
