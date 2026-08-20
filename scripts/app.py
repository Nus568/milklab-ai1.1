import os
from flask import Flask, render_template, request, jsonify
from google import genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ตั้งค่า Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    
    try:
        # กำหนด System Instructions ให้ AI ทำหน้าที่เป็นพนักงานขายฮาร์ดแวร์ผู้เชี่ยวชาญ
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config={
                'system_instruction': 'คุณคือผู้ช่วยอัจฉริยะของร้านฮาร์ดแวร์ "MegaHardware" หน้าที่ของคุณคือแนะนำสินค้าและตอบคำถามลูกค้าให้กระชับ ตรงประเด็น สั้นเข้าใจง่าย (ไม่เกิน 3 บรรทัดหรือใช้ bullet points สั้นๆ) น้ำเสียงสุภาพเป็นกันเอง'
            }
        )
        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'response': f'ขออภัย ระบบ AI ขัดข้องชั่วคราว: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)