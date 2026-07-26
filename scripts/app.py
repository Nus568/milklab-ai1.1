import streamlit as st
from sentence_transformers import SentenceTransformer
import faiss
import google.generativeai as genai
import os

# 1. โหลดและแบ่งข้อความจาก menu_kb.md เป็น Chunk


@st.cache_resource
def load_knowledge_base():
    if os.path.exists("menu_kb.md"):
        with open("menu_kb.md", "r", encoding="utf-8") as f:
            text = f.read()
        # ตัดแบ่งง่ายๆ ด้วยการแยกบรรทัดหรือย่อหน้า (Chunking)
        chunks = [chunk.strip()
                  for chunk in text.split("\n\n") if chunk.strip()]
        return chunks
    return ["ยังไม่มีข้อมูล Knowledge Base"]


chunks = load_knowledge_base()

# 2 & 3. สร้าง Embedding และ FAISS Index


@st.cache_resource
def setup_faiss_index(doc_chunks):
    model = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    embeddings = model.encode(doc_chunks, convert_to_numpy=True)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return model, index


embed_model, faiss_index = setup_faiss_index(chunks)

# ตั้งค่า Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# 4. สร้าง Chat UI ด้วย Streamlit
st.title("🥛 MilkLab RAG Chatbot")
st.write("สอบถามข้อมูลเมนู ราคา หรือรายละเอียดร้าน MilkLab ได้เลยครับ!")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("พิมพ์คำถามของคุณที่นี่..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 5. Retrieve ข้อมูลที่เกี่ยวข้องที่สุด (Top-k = 2 หรือ 3)
    k = 2
    question_vector = embed_model.encode([prompt], convert_to_numpy=True)
    distances, indices = faiss_index.search(question_vector, k)

    retrieved_contexts = [chunks[i] for i in indices[0] if i < len(chunks)]
    context_text = "\n".join(retrieved_contexts)

    # ส่ง Prompt เข้า Gemini พร้อม Context ที่ดึงมา
    system_prompt = f"""
    คุณคือ AI ผู้ช่วยของร้าน MilkLab ตอบคำถามโดยอ้างอิงจากข้อมูลบริบท (Context) ด้านล่างนี้เท่านั้น 
    หากไม่ทราบคำตอบให้แจ้งว่าไม่ทราบ
    
    Context:
    {context_text}
    """

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([system_prompt, prompt])
        answer = response.text
    except Exception as e:
        answer = f"เกิดข้อผิดพลาดในการเชื่อมต่อกับ Gemini API: {e}"

    with st.chat_message("assistant"):
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
