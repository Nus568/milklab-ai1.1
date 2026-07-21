# agent_harness.py
import os
import google.generativeai as genai
from agent_tools import log_sales, get_daily_summary, check_product_info

# โหลด API Key (ดึงจาก .env โดยอัตโนมัติ)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Guardrail 3: System Prompt (กำหนดขอบเขตและบุคลิกของ Agent อย่างเคร่งครัด)
SYSTEM_INSTRUCTION = """
คุณคือ "MilkLab Agent" ผู้ช่วยส่วนตัวสำหรับจัดการร้านค้า
กฎการทำงาน (Guardrails):
1. คุณต้องใช้ Tools ที่เตรียมไว้ให้เพื่อตอบคำถามเกี่ยวกับยอดขายหรือสินค้าเท่านั้น ห้ามแต่งข้อมูลขึ้นมาเองเด็ดขาด
2. หากผู้ใช้ถามเรื่องที่อยู่นอกเหนือจากการขายหรือการจัดการร้าน ให้ตอบกลับอย่างสุภาพว่า "ผมสามารถช่วยเหลือได้เฉพาะเรื่องการจัดการร้าน MilkLab เท่านั้นครับ"
3. ตอบกลับด้วยภาษาที่เป็นกันเอง สั้น กระชับ และเป็นมืออาชีพ
4. หากผู้ใช้สั่งบันทึกยอดขาย ให้ตรวจสอบความถูกต้องของข้อมูล (ชื่อสินค้า, จำนวน) ก่อนเสมอ ถ้าข้อมูลไม่ครบ ให้ถามกลับ
"""

# สร้าง Model และผูก Tools
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    tools=[log_sales, get_daily_summary, check_product_info],
    system_instruction=SYSTEM_INSTRUCTION
)

# เปิดใช้งาน Automatic Function Calling (ReAct Loop อัตโนมัติ)
chat_session = model.start_chat(enable_automatic_function_calling=True)


def process_user_message(user_message: str) -> str:
    """ฟังก์ชันสำหรับส่งข้อความไปหา Agent และรับคำตอบกลับมา"""
    try:
        response = chat_session.send_message(user_message)
        return response.text
    except Exception as e:
        # Guardrail 4: Graceful Error Handling
        return f"⚠️ ระบบ AI ขัดข้องชั่วคราว: {str(e)}"
