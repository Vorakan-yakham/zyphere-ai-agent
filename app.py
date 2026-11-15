import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

st.set_page_config(page_title="Zyphere Native Super-Agent", page_icon="🛡️", layout="centered")

# --- ดีไซน์สไตล์ Cyberpunk Command Center ---
st.markdown("""
    <style>
    .stApp { background-color: #090a0f; color: #e6edf3; }
    .main-title { font-size: 26px; font-weight: 800; color: #38bdf8; text-align: center; }
    .sub-title { color: #94a3b8; font-size: 14px; text-align: center; margin-bottom: 25px; }
    .stChatMessage { background-color: #1e293b !important; border-radius: 12px !important; padding: 15px !important; }
    [data-testid="stChatInput"] textarea { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🛡️ Zyphere Native Autonomous Business Engine</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">ระบบสร้างรายได้และประมวลผลภายใน (Independent Core)</p>', unsafe_allow_html=True)

# ฐานข้อมูลผู้มีสิทธิ์เด็ดขาด
AUTHORIZED_USERS = [
    {"name": "วรกันต์", "surname": "ยาคำ", "role": "Father"},
    {"name": "การัณยภาส", "surname": "ยาคำ", "role": "Son"}
]

if "is_verified" not in st.session_state:
    st.session_state.is_verified = False
    st.session_state.verified_name = ""

# ระบบความปลอดภัย
if not st.session_state.is_verified:
    st.subheader("🔑 ยืนยันตัวตนเจ้าของระบบ")
    c1, c2 = st.columns(2)
    with c1: in_name = st.text_input("ชื่อจริง", placeholder="วรกันต์")
    with c2: in_sur = st.text_input("นามสกุล", placeholder="ยาคำ")
    
    if st.button("🔓 ปลดล็อกระบบ", type="primary"):
        if any(u["name"] == in_name.strip() and u["surname"] == in_sur.strip() for u in AUTHORIZED_USERS):
            st.session_state.is_verified = True
            st.session_state.verified_name = in_name.strip()
            st.rerun()
        else:
            st.error("🚨 [ACCESS DENIED]: ปฏิเสธการเข้าถึงเฉพาะตระกูลยาคำเท่านั้น")
    st.stop()

speaker_name = st.session_state.verified_name
st.success(f"🛡️ ผู้ใช้งานปัจจุบัน: คุณ {speaker_name} | สถานะระบบ: Native Core Online")

# --- ฟังก์ชันสร้างและประมวลผลภายใน (Native Business Procedures) ---
def native_financial_calculator(principal, rate, years):
    """ฟังก์ชันคำนวณสินเชื่อและผลตอบแทนธุรกิจแบบคำนวณเอง 100%"""
    try:
        p = float(principal)
        r = float(rate) / 100 / 12
        n = int(years) * 12
        if r > 0:
            emi = (p * r * (1 + r)**n) / ((1 + r)**n - 1)
            total_payment = emi * n
            total_interest = total_payment - p
        else:
            emi = p / n
            total_payment = p
            total_interest = 0
        return emi, total_payment, total_interest
    except:
        return 0, 0, 0

st.markdown("---")
st.subheader("📊 ระบบบริการคำนวณและสร้างรายได้อัตโนมัติ (Native Micro-SaaS)")

tool_choice = st.selectbox("เลือกโมดูลบริการสำหรับลูกค้ายุคดิจิทัล:", [
    "1. ระบบคำนวณสินเชื่อและวางแผนการเงินธุรกิจ (Loan & EMI Engine)",
    "2. ระบบประเมินจุดคุ้มทุนและกำไรสินค้าออนไลน์ (Break-Even Profit Engine)"
])

if "1" in tool_choice:
    st.markdown("### 🧮 โมดูลคำนวณสินเชื่อ (พร้อมส่งออกรายงานให้ลูกค้า)")
    p_input = st.number_input("ยอดเงินกู้ / เงินลงทุนตั้งต้น (บาท):", value=100000.0, step=10000.0)
    r_input = st.number_input("อัตราดอกเบี้ยต่อปี (%):", value=5.0, step=0.5)
    y_input = st.number_input("ระยะเวลา (ปี):", value=3, step=1)
    
    if st.button("🚀 ประมวลผลและสร้างรายงานให้ลูกค้า", type="primary"):
        emi, total_pay, total_int = native_financial_calculator(p_input, r_input, y_input)
        
        report_text = f"""
        ### 📄 รายงานผลการคำนวณทางการเงิน (Zyphere Native Engine)
        - **ผู้จัดทำระบบ:** ออกแบบและประมวลผลโดย Zyphere สำหรับคุณ {speaker_name}
        - **ยอดเงินลงทุน/เงินกู้:** {p_input:,.2f} บาท
        - **ระยะเวลาผ่อนชำระ:** {y_input} ปี ({y_input*12} เดือน)
        - **ยอดผ่อนชำระต่อเดือน:** **{emi:,.2f} บาท/เดือน**
        - **ดอกเบี้ยรวมทั้งหมด:** {total_int:,.2f} บาท
        - **ยอดชำระสุทธิรวม:** {total_pay:,.2f} บาท
        
        *คำแนะนำเชิงธุรกิจ: ท่านสามารถบันทึกรายงานนี้ส่งให้ลูกค้าเพื่อปิดการขายบริการคำนวณสินเชื่อได้ทันที!*
        """
        st.success("✅ ประมวลผลสำเร็จเรียบร้อย!")
        st.markdown(report_text)

elif "2" in tool_choice:
    st.markdown("### 📦 โมดูลประเมินจุดคุ้มทุนร้านค้าออนไลน์")
    cost_per_unit = st.number_input("ต้นทุนสินค้าต่อชิ้น (บาท):", value=50.0)
    sell_price = st.number_input("ราคาขายต่อชิ้น (บาท):", value=150.0)
    fixed_cost = st.number_input("ค่าใช้จ่ายคงที่ต่อเดือน เช่น ค่าโฆษณา/ค่าเช่า (บาท):", value=5000.0)
    
    if st.button("🚀 คำนวณจุดคุ้มทุนธุรกิจ", type="primary"):
        profit_per_unit = sell_price - cost_per_unit
        if profit_per_unit > 0:
            break_even_units = fixed_cost / profit_per_unit
            st.success("✅ คำนวณสำเร็จ!")
            st.markdown(f"""
            ### 📈 รายงานจุดคุ้มทุน (Break-Even Analysis)
            - **กำไรต่อชิ้น:** {profit_per_unit:,.2f} บาท
            - **จำนวนสินค้าที่ต้องขายได้ต่อเดือนเพื่อให้คุ้มทุน:** **{break_even_units:,.0f} ชิ้น**
            
            *บริการนี้เหมาะสำหรับนำไปรับจ้างปรึกษาพ่อค้าแม่ค้าออนไลน์ในการตั้งราคาขายครับ!*
            """)
        else:
            st.error("❌ ราคาขายต้องมากกว่าต้นทุนสินค้าจึงจะสามารถคำนวณจุดคุ้มทุนได้")
