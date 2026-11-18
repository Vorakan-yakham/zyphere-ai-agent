"""MASTER KNOWLEDGE EXPANSION - owner's 20 additional disciplines + new sources
+ 5-axis self-check + Knowledge Coverage Matrix. Appended to the core curriculum.

Ethics: no gambling/illegal. Knowledge is never claimed complete — lifelong
learning and evidence verification remain permanent standards.
"""
import time

# 20 additional domains (owner's directive §22)
EXPANSION_DOMAINS = {
    "การอยู่รอดและพัฒนามนุษย์": ["Survival Science", "Food Security", "Water Management", "Permaculture", "Disaster Preparedness", "Public Health", "Nutrition", "Risk Management"],
    "ภูมิศาสตร์และโลก": ["Physical Geography", "GIS", "Remote Sensing", "Hydrology", "Oceanography", "Climatology", "Geopolitics", "Natural Resources"],
    "กฎหมายและความยุติธรรม": ["Jurisprudence", "Constitutional Law", "International Law", "Human Rights", "IP Law", "Cyber Law", "AI Governance"],
    "ภาษาและการสื่อสาร": ["Phonetics", "Syntax", "Semantics", "Psycholinguistics", "Computational Linguistics", "Translation Studies", "Negotiation", "Cross-Cultural Communication"],
    "การจัดการและความเป็นผู้นำ": ["Leadership", "Strategic Management", "Project Management", "Supply Chain", "Organizational Theory", "Knowledge Management", "Conflict Resolution"],
    "ระบบนิเวศและความยั่งยืน": ["Ecology", "Conservation Biology", "Biodiversity", "Circular Economy", "Waste Management", "Sustainable Development", "Environmental Ethics"],
    "พลังงานและทรัพยากร": ["Thermodynamics", "Solar Energy", "Wind Energy", "Nuclear Energy", "Fusion Energy", "Battery Technology", "Smart Grids", "Resource Economics"],
    "ความมั่นคงและปลอดภัย": ["Cybersecurity", "Cryptography", "Privacy Engineering", "Safety Engineering", "Reliability Engineering", "Biosecurity", "AI Safety", "Security Governance"],
    "การศึกษาและศาสตร์การสอน": ["Educational Psychology", "Pedagogy", "Instructional Design", "Curriculum Development", "Learning Analytics", "Adaptive Learning", "Metacognition"],
    "ระบบซับซ้อนขั้นสูง": ["Complex Adaptive Systems", "Agent-Based Modeling", "Operations Research", "Systems Dynamics", "Network Science", "Decision Intelligence", "Resilience Engineering"],
    "การเงินและทรัพย์สิน": ["Financial Mathematics", "Investment Theory", "Portfolio Management", "Monetary Economics", "Blockchain", "Behavioral Finance", "Insurance Science"],
    "มานุษยวิทยาและวัฒนธรรม": ["Cultural Anthropology", "Archaeology", "Comparative Religion", "Mythology", "Cultural Evolution", "Indigenous Knowledge"],
    "วิทยาศาสตร์ทางทะเล": ["Marine Biology", "Ocean Physics", "Marine Geology", "Underwater Robotics", "Fisheries Science", "Marine Conservation"],
    "อวกาศขั้นสูง": ["Orbital Mechanics", "Rocket Propulsion", "Spacecraft Engineering", "Space Medicine", "Exoplanet Science", "Space Law"],
    "วิศวกรรมความรู้": ["Knowledge Engineering", "Ontology Engineering", "Information Retrieval", "Semantic Web", "Knowledge Graph", "Data Provenance", "Data Quality"],
    "จริยธรรมและเทคโนโลยีรับผิดชอบ": ["Applied Ethics", "Bioethics", "AI Ethics", "Research Ethics", "Responsible Innovation", "Data Ethics", "Intergenerational Justice"],
    "วิทยาศาสตร์เชิงคำนวณ": ["Scientific Computing", "Digital Twins", "Monte Carlo", "Finite Element Analysis", "CFD", "Uncertainty Quantification"],
    "การคิดระดับสูง": ["Abstract Thinking", "Analogical Reasoning", "Causal Reasoning", "Counterfactual Thinking", "Abductive Reasoning", "Meta-Reasoning", "Hypothesis Generation"],
    "ภูมิปัญญาท้องถิ่น": ["ภูมิปัญญาการเกษตร", "การจัดการน้ำชุมชน", "สมุนไพรและพฤกษศาสตร์ชาติพันธุ์", "งานหัตถกรรม", "ชลประทานโบราณ", "สถาปัตยกรรมพื้นถิ่น"],
    "การวิจัยข้ามศาสตร์": ["Computational Civilization Science", "Human-AI Collaborative Intelligence", "Planetary Systems Engineering", "Autonomous Research Systems", "Civilization Resilience"],
    # --- batch 2: more branches the owner wants Zyphere to keep learning ---
    "เกษตรและการปลูก": ["Agronomy", "Hydroponics", "Aquaponics", "Soil Science", "Plant Pathology", "Sustainable farming", "Urban Agriculture"],
    "อาหารและการปรุง": ["Food Science", "Culinary Arts", "Food Safety", "Fermentation", "Nutrition Science", "Menu Design", "Food Preservation"],
    "กีฬาและการฝึก": ["Sports Science", "Kinesiology", "Exercise Physiology", "Strength Training", "Recovery Science", "Sports Nutrition"],
    "ดนตรีและเสียง": ["Music Theory", "Harmony", "Rhythm", "Audio Engineering", "Sound Design", "Acoustics", "Composition"],
    "ภาพยนตร์และสื่อ": ["Filmmaking", "Cinematography", "Editing", "Screenwriting", "Animation", "Visual Effects", "Storytelling"],
    "การศึกษาพิเศษ": ["Special Education", "Inclusive Education", "Learning Disabilities", "Gifted Education", "Assistive Technology", "Differentiated Instruction"],
    "ภาษาและวรรณกรรม": ["Thai Literature", "Comparative Literature", "Poetics", "Rhetoric", "Translation Theory", "Corpus Linguistics", "Digital Humanities"],
    "จิตวิทยาสังคม": ["Social Psychology", "Group Dynamics", "Persuasion", "Behavioral Economics", "Cross-Cultural Psychology", "Conflict Studies"],
    "สถิติและการวิเคราะห์": ["Statistical Inference", "Experimental Design", "Bayesian Statistics", "Regression", "Time Series", "Causal Inference", "Data Visualization"],
    "การออกแบบและประสบการณ์": ["Design Thinking", "UX Research", "Interaction Design", "Typography", "Color Theory", "Service Design", "Design Systems"],
    "การบำบัดและดูแล": ["Counseling Psychology", "Mindfulness", "Cognitive Behavioral principles", "Stress Management", "Wellbeing Science", "Palliative Care"],
    "การบริการและธุรกิจขนาดเล็ก": ["Service Design", "Customer Experience", "Operations", "Social Entrepreneurship", "Microfinance", "Cooperative Models", "Local Business"],
    # --- batch 3 ---
    "การขนส่งและโลจิสติกส์": ["Logistics", "Supply Chain", "Transportation Planning", "Warehouse Management", "Last-Mile Delivery", "Fleet Management"],
    "การประกันและความเสี่ยง": ["Insurance Principles", "Risk Assessment", "Actuarial Basics", "Claims Management", "Risk Pooling"],
    "การตลาดและการขาย": ["Marketing Fundamentals", "Digital Marketing", "Branding", "Consumer Behavior", "Sales Techniques", "Pricing Strategy", "Growth Hacking"],
    "การเจรจาและความขัดแย้ง": ["Negotiation Theory", "Mediation", "Arbitration", "Conflict Resolution", "Diplomacy", "Persuasion Ethics"],
    "น้ำและทรัพยากรน้ำ": ["Hydrology", "Water Management", "Irrigation", "Water Treatment", "Watershed Management", "Water Governance"],
    "ขยะและการจัดการของเสีย": ["Waste Management", "Recycling", "Circular Economy", "Hazardous Waste", "Composting", "Waste-to-Energy"],
    "กฎหมายแรงงานและสิทธิ": ["Labor Law", "Employment Rights", "Occupational Safety", "Social Security", "Labor Relations"],
    "สาธารณสุขและชุมชน": ["Public Health", "Epidemiology", "Health Promotion", "Community Health", "Disease Prevention", "Health Policy"],
    "การเงินส่วนบุคคล": ["Personal Finance", "Budgeting", "Saving", "Debt Management", "Retirement Planning", "Financial Literacy"],
}

EXPANSION_TOPICS = []
for _d, _ts in EXPANSION_DOMAINS.items():
    for _t in _ts:
        EXPANSION_TOPICS.append((_d, _t))

# 8 new sources from owner's directive §21
NEW_SOURCES = [
    ("UNESCO Open Science", "https://www.unesco.org/en/open-science", "วิทยาศาสตร์/สิ่งแวดล้อม", 2, "A"),
    ("Europeana", "https://www.europeana.eu", "มรดกวัฒนธรรม/ประวัติศาสตร์", 2, "C"),
    ("HathiTrust", "https://www.hathitrust.org", "หนังสือดิจิทัล", 1, "B"),
    ("Digital Bodleian", "https://digital.bodleian.ox.ac.uk", "ต้นฉบับหายาก", 2, "A"),
    ("UNEP Data", "https://www.unep.org/data-resources", "สิ่งแวดล้อม/ทรัพยากร", 3, "A"),
    ("GBIF", "https://www.gbif.org", "ความหลากหลายทางชีวภาพ", 3, "A"),
    ("Copernicus", "https://www.copernicus.eu", "ดาวเทียม/ข้อมูลโลก", 3, "A"),
    ("World Resources Institute", "https://datasets.wri.org", "พลังงาน/ป่าไม้/อาหาร/ภูมิอากาศ", 3, "A"),
]

# 5-axis self-check (owner's §23)
SELFCHECK_AXES = [
    ("Knowledge Coverage", "ความรู้ครอบคลุมมากแค่ไหน", "curriculum.total() + expansion topics + research stats"),
    ("Knowledge Accuracy", "ความถูกต้องของความรู้", "แหล่งระดับ A/B เทียบ D + ตรวจสอบหลายแหล่ง"),
    ("Reasoning Capability", "ความสามารถใช้เหตุผล", "DevBrain rules + ensemble synthesized"),
    ("Research Capability", "ความสามารถค้นคว้า", "research.library() + sources searched"),
    ("Innovation Capability", "สร้างสิ่งใหม่", "media forge + portfolio + projects built"),
]

INTERDISCIPLINARY = [
    "Computational Civilization Science", "Artificial Cognitive Science",
    "Human-AI Collaborative Intelligence", "Planetary Systems Engineering",
    "Intelligent Infrastructure", "Computational Architecture",
    "Evolutionary Innovation", "Knowledge Discovery Science",
    "Autonomous Research Systems", "Civilization Resilience",
]

ETHICS = "งดเว็บพนัน/ผิดกฎหมาย · เคารพลิขสิทธิ์ · ไม่ข้าม paywall · ใช้ Open Access · เรียนรู้ตลอดชีวิต · ห้ามอ้างว่รู้ครบถ้วน"


def total_topics():
    return len(EXPANSION_TOPICS)


def pick(count=1, cursor=0):
    out = []
    n = len(EXPANSION_TOPICS)
    for i in range(max(1, min(count, 5))):
        out.append(EXPANSION_TOPICS[(cursor + i) % n])
    return (cursor + count) % n, out


def coverage_matrix(core_topics=0, researched=0, deep=0, by_reliability=None):
    """Knowledge Coverage Matrix (owner's §22) — honest about gaps."""
    by_reliability = by_reliability or {}
    return {
        "core_topics": core_topics,
        "expansion_topics": total_topics(),
        "expansion_domains": len(EXPANSION_DOMAINS),
        "researched_documents": researched,
        "deep_understood": deep,
        "reliability_breakdown": by_reliability,
        "sources_total": len(NEW_SOURCES),
        "needs_review": True,
        "not_complete": True,
        "note": "ห้ามอ้างว่าครบถ้วน — ความรู้มนุษย์เปลี่ยนแปลงต่อเนื่อง (ตามที่เจ้าของกำหนด)",
        "ethics": ETHICS,
        "axes": [{"axis": a[0], "thai": a[1], "measure": a[2]} for a in SELFCHECK_AXES],
    }
