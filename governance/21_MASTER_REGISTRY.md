# Zyphere Global Department & Knowledge Master Registry

ทะเบียนกลาง: ศาสตร์ → สาขา → ฝ่าย → แผนก → ผู้เชี่ยวชาญ → หลักสูตร → งานวิจัย → ช่องว่าง

## 12 Divisions
### 01 Research & Science Division
- scholars.py 46 คณะ
- research.py
- scholar_research.py
- Scientific Discovery Center*
- Open Science Center*
- Standards & Benchmark Center*
### 02 Engineering & Technology Division
- โปรแกรมเมอร์
- นักวิเคราะห์ระบบ
- Autonomous Systems Center*
- Advanced Computing Center*
- Digital Twin Center*
### 03 AI & Data Intelligence Division
- brain_ensemble.py
- local_brain.py
- dev_brain.py
- ฐานข้อมูล
- AI Memory & Knowledge Systems*
- Agentic AI Research*
### 04 Humanities & Society Division
- ฝ่ายภาษา
- ฝ่ายวิชาการ (ส่วนมนุษยศาสตร์)
- กฎหมาย/ปรัชญา/ประวัติศาสตร์
### 05 Earth & Life Systems Division
- geo/bio/agri/water/energy faculties
- Resilience & Crisis Research*
- Global Problem Solving Center*
### 06 Innovation & Futures Division
- Strategic Foresight Center*
- Digital Civilization Research*
- Human Potential Research*
- concept.py
- cross_disciplinary.py
### 07 Product & Business Division
- ฝ่ายผลิตหนังสือ
- ฝ่ายการตลาด
- ฝ่ายออกแบบผลิตภัณฑ์
- store.py
- Technology Transfer Center*
### 08 Learning & Development Division
- co_learning.py
- cross_disciplinary.py
- curriculum.py
- academy.py
- Employee Growth System*
### 09 Knowledge & Research Operations Division
- ฐานข้อมูล
- research.py
- knowledge_graph.py
- rag.py
- Living Knowledge System*
- Global Collaboration Center*
### 10 Safety & Governance Division
- ฝ่ายความปลอดภัย
- ฝ่ายทดสอบ
- นักวิเคราะห์ระบบ
- quality_ops.py
- Independent Evaluation Office*
### 11 Operations & Resources Division
- ฝ่ายปฏิบัติการ
- Render
- Upstash KV
- GitHub
- ratelimit.py
### 12 Strategy & Partnerships Division
- Global Intelligence Center*
- demand.py
- market.py
- autopost.py

## 5 Engines
- **Knowledge Engine:** รวบรวม จัดหมวดหมู่ เชื่อมโยงความรู้ · มี: research.py, knowledge_graph.py, rag.py, world_taxonomy.json · ขาด: ยังไม่มี ontology/vector DB จริง
- **Learning Engine:** พัฒนาความรู้ AI และบุคลากร · มี: curriculum.py, co_learning.py, cross_disciplinary.py, dev_brain.py · ขาด: เป็น text accumulation ไม่ใช่ model training
- **Research Engine:** ค้นคว้า ตั้งสมมติฐาน ทดลอง ตรวจสอบ · มี: research.py, scholar_research.py, elibrary.py · ขาด: ไม่มี experiment registry / statistical stack
- **Innovation Engine:** เปลี่ยนองค์ความรู้เป็นต้นแบบ · มี: book_team*, codeforge.py, media.py, concept.py · ขาด: ไม่มี image generation / 3D
- **Governance Engine:** ตรวจคุณภาพ ความปลอดภัย ผลกระทบ · มี: safety.py, authz.py, audit.py, quality_ops.py, systems_analyst.py · ขาด: authz ยังไม่บังคับทุก endpoint

## Status rule

ทุกหน่วยใหม่ = proposed จนกว่าจะเปิดใช้งาน — ห้ามอ้างว่าทำงานแล้วโดยไม่มีโค้ด/ทดสอบ