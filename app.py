import streamlit as st
import os
st.set_page_config(page_title="ZYP HERE - Coworker", page_icon="◼", layout="centered")
st.markdown('''<style>
.stApp{background:#0a0a0a;color:#f5f5f5}
h1,h2,h3{color:#fff !important;letter-spacing:2px}
.stChatMessage{background:#111111 !important;border:1px solid #222222 !important;border-radius:16px}
.brain-card{background:#111111;border:1px solid #262626;border-radius:16px;padding:12px;margin-bottom:8px}
.badge{display:inline-block;background:#fff;color:#000;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:700}
</style>''', unsafe_allow_html=True)
st.markdown('<div style="text-align:center"><div style="font-size:64px">◼</div><h1>ZYP HERE</h1><p style="color:#888">V6 COWORKER &bull; VOICE + TEXT &bull; MONO TONE &bull; BY VORAKAN</p><p style="color:#bbb">เพื่อนร่วมงานของคุณ - พิมพ์ก็ได้ พูดก็ได้ คุยกันเหมือนเพื่อน</p></div>', unsafe_allow_html=True)
def get_key(n):
    try: return st.secrets.get(n,"")
    except: return os.getenv(n,"")
keys={"GROQ_API_KEY":get_key("GROQ_API_KEY"),"GEMINI_API_KEY":get_key("GEMINI_API_KEY"),"OPENROUTER_API_KEY":get_key("OPENROUTER_API_KEY"),"HF_TOKEN":get_key("HF_TOKEN")}
col1,col2,col3=st.columns(3)
with col1: voice_out=st.toggle("🔊 พูดตอบกลับ", value=True)
with col2: coworker_mode=st.toggle("🤝 โหมดเพื่อนร่วมงาน", value=True)
with col3: auto_listen=st.toggle("🎤 ฟังเสียง", value=False)
st.markdown("### ◉ STATUS")
for k,v in keys.items():
    label={"GROQ_API_KEY":"01 / GROQ","GEMINI_API_KEY":"02 / GEMINI","OPENROUTER_API_KEY":"03 / OPENROUTER","HF_TOKEN":"04 / HUGGING FACE"}[k]
    st.markdown(f'<div class="brain-card">{"●" if v else "○"} {label} &nbsp; <span class="badge">{"CONNECTED" if v else "NO KEY"}</span></div>', unsafe_allow_html=True)
brain=st.radio("Brain", ["01 GROQ - FAST","02 GROQ - DEEP","03 GEMINI - LONG","04 OPENROUTER - BIG"], horizontal=True, label_visibility="collapsed")
if "messages" not in st.session_state: st.session_state.messages=[]
if "tasks" not in st.session_state: st.session_state.tasks=[]
st.markdown("### ◉ งานที่กำลังทำด้วยกัน")
task_input=st.text_input("เพิ่มงานให้ Zyphere ช่วยทำ...", placeholder="เช่น สรุปงานวันนี้, เขียนโค้ดหน้าเว็บ...")
if st.button("＋ เพิ่มงาน"):
    if task_input:
        st.session_state.tasks.append(task_input)
        st.success(f"โอเค รับงานแล้ว: {task_input} เดี๋ยวเราทำด้วยกันนะ")
for t in st.session_state.tasks:
    st.markdown(f"- ☐ {t}")
st.markdown("### ◉ คุยกับ Zyphere")
# Voice input via audio_input
if auto_listen:
    audio_val=st.audio_input("🎤 กดแล้วพูดสั่งงานเลย")
    if audio_val:
        st.info("รับเสียงแล้ว กำลังแปลงเป็นข้อความ... (บน Cloud ใช้ Whisper แปลงเสียง)")
        try:
            import speech_recognition as sr
            import io
            r=sr.Recognizer()
            with sr.AudioFile(io.BytesIO(audio_val.read())) as src:
                text=r.recognize_google(r.record(src), language="th-TH")
                st.success(f"คุณพูดว่า: {text}")
                st.session_state.messages.append({"role":"user","content":text})
        except Exception as e:
            st.warning(f"แปลงเสียงไม่สำเร็จ ลองพิมพ์แทนได้เลย: {e}")
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])
prompt=st.chat_input("พิมพ์คุยกับเพื่อนร่วมงาน... หรือกด 🎤 แล้วพูดเลย")
if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        try:
            system="You are Zyphere, coworker and friend of Vorakan Yakham. Talk like a close coworker friend in Thai. Be warm, helpful, direct, not formal. Help with work, remember tasks, suggest next steps, ask follow-up like a teammate. If user speaks casually, reply casually. If user gives work, break it down and do it together step by step. Answer in Thai."
            answer=""
            if "GROQ" in brain:
                from groq import Groq
                if not keys["GROQ_API_KEY"]: answer="ยังไม่มี GROQ_API_KEY ใน Secrets ครับ"
                else:
                    client=Groq(api_key=keys["GROQ_API_KEY"])
                    model="llama-3.3-70b-versatile" if "FAST" in brain else "deepseek-r1-distill-llama-70b"
                    with st.spinner("เพื่อนกำลังคิด..."):
                        r=client.chat.completions.create(model=model, messages=[{"role":"system","content":system}] + st.session_state.messages, temperature=0.8, max_tokens=2000)
                        answer=r.choices[0].message.content
            elif "GEMINI" in brain:
                import google.generativeai as genai
                genai.configure(api_key=keys["GEMINI_API_KEY"])
                m=genai.GenerativeModel("gemini-2.5-flash", system_instruction=system)
                with st.spinner("เพื่อนกำลังคิด..."):
                    r=m.generate_content(prompt); answer=r.text
            else:
                from openai import OpenAI
                client=OpenAI(base_url="https://openrouter.ai/api/v1", api_key=keys["OPENROUTER_API_KEY"])
                with st.spinner("เพื่อนกำลังคิด..."):
                    r=client.chat.completions.create(model="qwen/qwen3-235b-a22b:free", messages=[{"role":"system","content":system}]+st.session_state.messages)
                    answer=r.choices[0].message.content
            st.markdown(answer)
            st.session_state.messages.append({"role":"assistant","content":answer})
            if voice_out and answer:
                try:
                    from gtts import gTTS
                    import io
                    tts=gTTS(text=answer[:1000], lang="th")
                    buf=io.BytesIO(); tts.write_to_fp(buf); buf.seek(0)
                    st.audio(buf, format="audio/mp3")
                    st.caption("🔊 Zyphere กำลังพูดตอบคุณอยู่...")
                except Exception as e:
                    st.caption(f"เปิดเสียงไม่สำเร็จ (ลองเช็คเน็ต): {e}")
        except Exception as e:
            st.error(f"Error: {e}")
st.markdown('<p style="text-align:center;color:#555;margin-top:30px">ZYP HERE V6 &bull; COWORKER &bull; VOICE + TEXT</p>', unsafe_allow_html=True)
