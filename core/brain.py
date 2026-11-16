import ollama

def ask_zyphere(messages, model="qwen3:14b"):
    response = ollama.chat(
        model=model,
        messages=messages,
        stream=True,
        options={"temperature": 0.3}
    )
    return response
