# เก็บไว้ใช้บนเครื่องตัวเองเท่านั้น
try:
    import ollama
    def ask_zyphere(messages, model="qwen3:14b"):
        return ollama.chat(model=model, messages=messages, stream=True, options={"temperature": 0.3})
except:
    def ask_zyphere(messages, model="qwen3:14b"):
        raise RuntimeError("ไม่มี Ollama บนเครื่องนี้")
