def calculate(expr: str):
    try:
        return str(eval(expr))
    except:
        return "คำนวณไม่ได้ครับ"
