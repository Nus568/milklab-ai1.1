import os
import google.generativeai as genai
from dotenv import load_dotenv

# โหลด API Key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("🔍 รายชื่อโมเดลที่บัญชีของคุณรองรับ (สามารถใช้สร้างข้อความได้):")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f" - {m.name}")
