"""MilkLab Agent Harness (S2).

Usage:
    python agent_harness.py --cmd "บันทึกขายนมหมี 2 ขวด ขวดละ 65"

รับคำสั่งภาษาไทย ส่งให้ Gemini พร้อม tool schema parse response เป็น tool call
เรียก tool จริง print trace log

นักศึกษาต้องเติม TODO ใน 3 จุด ใน Session 2 Lab 2.3
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv
from google import genai
from agent_tools import TOOL_REGISTRY  # เพิ่มการนำเข้าคลังอาวุธที่เราสร้างไว้

TOOL_SCHEMA = [
    {
        "name": "log_sale",
        "description": "บันทึกการขายลง Google Sheets และส่ง notification",
        "parameters": {
            "type": "object",
            "properties": {
                "menu": {"type": "string", "description": "ชื่อเมนู"},
                "qty": {"type": "integer", "description": "จำนวนที่ขาย"},
                "price": {"type": "number", "description": "ราคาต่อหน่วย"},
            },
            "required": ["menu", "qty", "price"],
        },
    },
    {
        "name": "query_sales",
        "description": "ดูยอดขายของวันที่ระบุ",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "วันที่ format YYYY-MM-DD"},
            },
            "required": ["date"],
        },
    },
    {
        "name": "send_alert",
        "description": "ส่ง message แจ้งเตือนผ่าน Bot",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
            },
            "required": ["message"],
        },
    },
]


def parse_command(cmd: str, api_key: str | None = None) -> dict:
    """TODO 1: ส่ง cmd ไป Gemini พร้อม TOOL_SCHEMA ขอให้ตอบเป็น JSON {tool, args}"""
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("ไม่พบ GEMINI_API_KEY ในไฟล์ .env หรือ Environment")

    client = genai.Client(api_key=api_key)
    
    # สร้าง Prompt บังคับให้ AI ตอบกลับมาเป็น JSON ตามที่เรากำหนด
    prompt = f"""
    คุณคือผู้ช่วยร้าน MilkLab หน้าที่ของคุณคือเลือก tool ที่เหมาะสมที่สุดเพื่อทำตามคำสั่งของลูกค้า
    คำสั่งลูกค้า: "{cmd}"

    Tools ที่มีให้เลือกใช้งาน:
    {json.dumps(TOOL_SCHEMA, ensure_ascii=False, indent=2)}

    จงวิเคราะห์คำสั่งและเลือก tool ที่ถูกต้อง พร้อมดึงข้อมูลมาเป็น argument
    ตอบกลับด้วย JSON Format เท่านั้น (ห้ามมีคำอธิบายเพิ่มเติม และห้ามครอบด้วย ```json):
    {{
        "tool": "ชื่อ tool ที่เลือก",
        "args": {{
            "พารามิเตอร์ 1": "ค่าที่ดึงมา",
            "พารามิเตอร์ 2": "ค่าที่ดึงมา"
        }}
    }}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        # ทำความสะอาดข้อความ (กรณี AI เผลอส่ง Markdown ติดมา)
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text.rsplit("\n", 1)[0]
            
        return json.loads(raw_text.strip())
    
    except Exception as e:
        raise RuntimeError(f"Parse JSON จาก LLM ไม่สำเร็จ: {e}")


def dispatch_tool(tool_call: dict) -> str:
    """TODO 2: เรียก tool ตาม tool_call["tool"] ด้วย args จริง"""
    tool_name = tool_call.get("tool")
    args = tool_call.get("args", {})

    # เช็คว่ามี Tool นี้อยู่ในระบบที่เราสร้างไว้ไหม
    if tool_name not in TOOL_REGISTRY:
        return f'{{"ok": false, "error": "ไม่พบ Tool ชื่อ {tool_name} ในระบบ"}}'

    # ดึงฟังก์ชันออกมาจาก Registry
    tool_func = TOOL_REGISTRY[tool_name]['fn']

    try:
        # สั่งรันฟังก์ชันพร้อมโยนค่า args เข้าไป (unpack dictionary)
        result = tool_func(**args)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return f'{{"ok": false, "error": "รัน Tool ล้มเหลว - {e}"}}'


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--cmd", required=True, help="คำสั่งภาษาไทย")
    args = parser.parse_args()

    print(f"[USER] {args.cmd}")

    try:
        # TODO 3: รันตามลำดับ Parse -> Dispatch -> Print
        tool_call = parse_command(args.cmd)
        print(f"[LLM]  tool={tool_call['tool']} args={tool_call['args']}")

        result = dispatch_tool(tool_call)
        print(f"[TOOL] {tool_call['tool']} {result}")
        
        # ถอด JSON ผลลัพธ์เพื่อโชว์ข้อความให้ User อ่านง่ายๆ
        res_dict = json.loads(result)
        if res_dict.get('ok'):
            print(f"[USER] ← {res_dict.get('msg', 'สำเร็จ')}")
        else:
            print(f"[USER] ← เกิดข้อผิดพลาด: {res_dict.get('error')}")
            
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())