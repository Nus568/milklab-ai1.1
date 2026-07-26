import streamlit as st
import google.generativeai as genai
import faiss
import numpy as np
import os

# 1. ตั้งค่าหน้าเพจ Streamlit
st.set_page_config(page_title="MilkLab AI", page_icon="🥛")
st.title("🥛 MilkLab AI Chatbot")

# 2. ตั้งค่า Gemini API Key (ดึงจาก Environment Variables ของ Render)
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error(
        "⚠️ ไม่พบ GEMINI_API_KEY กรุณาตรวจสอบการตั้งค่า Environment Variables ใน Render")
    st.stop()

genai.configure(api_key=api_key)

# 3. ฟังก์ชันสำหรับสร้างฐานข้อมูลเวกเตอร์ (ใช้ Gemini แทน sentence-transformers เพื่อประหยัด RAM)


@st.cache_resource
def build_knowledge_base():
    file_path = "menu_kb.md"
    if not os.path.exists(file_path):
        return None, None

    # อ่านไฟล์ข้อมูล
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # หั่นข้อความเป็นท่อนๆ (ย่อหน้า)
    chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]

    if not chunks:
        return None, None

    # แปลงข้อความเป็นเวกเตอร์ด้วย Gemini Embedding API (ไม่กิน RAM เครื่อง)
    embeddings = []
    for chunk in chunks:
        result = genai.embed_content(
            model="models/gemini-embedding-2",
            content=chunk,
            task_type="retrieval_document"
        )
        embeddings.append(result['embedding'])

    embeddings_array = np.array(embeddings, dtype='float32')

    # สร้างฐานข้อมูล FAISS
    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_array)

    return index, chunks


# โหลดฐานข้อมูล (รันครั้งเดียวและเก็บไว้ใน Cache)
index, chunks = build_knowledge_base()

if index is None:
    st.warning("⚠️ ยังไม่มีข้อมูล Knowledge Base หรือหาไฟล์ menu_kb.md ไม่พบ")
else:
    # 4. จัดการประวัติการแชท
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # แสดงประวัติการแชท
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 5. รับข้อความจากผู้ใช้และประมวลผล
    if user_query := st.chat_input("พิมพ์คำถามของคุณที่นี่..."):
        # แสดงข้อความผู้ใช้
        st.session_state.messages.append(
            {"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("กำลังคิดคำตอบ..."):
                try:
                    # แปลงคำถามผู้ใช้เป็นเวกเตอร์
                    query_embedding = genai.embed_content(
                        model="models/gemini-embedding-2",
                        content=user_query,
                        task_type="retrieval_query"
                    )['embedding']
                    query_vector = np.array([query_embedding], dtype='float32')

                    # ค้นหาข้อมูลที่เกี่ยวข้องที่สุด 3 อันดับแรก
                    k = 3
                    distances, indices = index.search(query_vector, k)

                    # นำข้อมูลที่ค้นพบมาต่อกันเป็น Context
                    context = "\n".join([chunks[i]
                                        for i in indices[0] if i < len(chunks)])

                    # สร้าง Prompt ให้ Gemini ตอบคำถามจากข้อมูลที่ค้นมาได้
                    prompt = f"""
                    คุณคือผู้ช่วย AI ของร้าน MilkLab ตอบคำถามโดยอ้างอิงจากข้อมูลด้านล่างนี้เท่านั้น
                    หากในข้อมูลไม่มีคำตอบ ให้บอกสุภาพๆ ว่าไม่ทราบข้อมูลนี้
                    
                    ข้อมูลอ้างอิง:
                    {context}
                    
                    คำถาม: {user_query}
                    """

                    # เรียกใช้ Gemini รุ่น 1.5 Flash เพื่อสร้างคำตอบ
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    response = model.generate_content(prompt)
                    bot_reply = response.text

                    # แสดงคำตอบ
                    st.markdown(bot_reply)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": bot_reply})

                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {str(e)}")
