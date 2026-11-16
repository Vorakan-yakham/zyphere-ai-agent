# ขั้นตอนใช้งาน (ไม่พึ่ง API คลาวด์)

1. ติดตั้ง Ollama (https://ollama.com) แล้วดึงโมเดล:
   ollama pull qwen2.5:7b-instruct      # แชท (เครื่อง RAM 16GB ใช้ได้; ถ้ามี GPU ใหญ่ลองรุ่น 14b/32b)
   ollama pull qwen2.5vl:7b             # (ถ้าต้องการให้ AI "มองภาพ" จากกล้อง)
2. pip install -r requirements.txt
3. ใน app.py:
   - เปลี่ยน import: from core.local_llm import LocalLLM, LLMError
     from core.stt_local import VoiceError, transcribe
     from core.tts_local import synthesize
     from core.sensors import analyze_image, summarize
   - แทน LLM(api_key, model) ด้วย LocalLLM(model)  (ทุกจุด รวม get_scheduler)
   - ลบ get_api_key / ตัวแปร online ให้ online = True (หรือเช็ก LocalLLM().models())
   - เสียงตอบ: audio = synthesize(answer); st.audio(audio, autoplay=True)
   - เซ็นเซอร์: img = st.camera_input("กล้อง"); if img: ctx = summarize(analyze_image(img.getvalue()))
     แล้วเติม ctx ต่อท้าย prompt ก่อนส่งให้โมเดล
   - คิดลึก: ใช้ core.reasoning.deliberate(llm, history, prompt, system)
4. ZyphereAdvancedEngine / Brain / commands ใน core/ ต้องปรับให้เรียก
   llm.stream(messages, system=...) และ llm.complete(...) แทนเมธอดของ Anthropic
