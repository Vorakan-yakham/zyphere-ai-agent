"""Zyphere Master Curriculum - derived from the owner's MASTER LEARNING DIRECTIVE.

19 domains, each with representative topics. The learn scheduler pulls from
this in rotation. Every topic is studied through the 15-step method from the
directive (not just passive reading).
"""
import time

LEARN_STEPS = [
    "ความหมายและคำศัพท์พื้นฐาน", "ประวัติความเป็นมา", "นักคิดและผู้ค้นพบสำคัญ",
    "หลักการพื้นฐาน", "ทฤษฎีที่เกี่ยวข้อง", "สมการและแบบจำลอง",
    "หลักฐานและงานวิจัย", "การประยุกต์ใช้งานจริง", "ข้อจำกัดและข้อผิดพลาด",
    "เชื่อมโยงกับศาสตร์อื่น", "ทดสอบความเข้าใจด้วยโจทย์", "สร้างผลงานจริง",
    "สรุปองค์ความรู้เป็นระบบ", "คำถามที่ยังไม่มีคำตอบ", "แนวทางวิจัยต่อยอด",
]

DOMAINS = {
    "ประวัติศาสตร์และอารยธรรม": [
        "วิวัฒนาการของมนุษย์", "จุดกำเนิดอารยธรรม", "อารยธรรมเมโสโปเตเมีย",
        "อียิปต์โบราณ", "กรีกและโรมัน", "อารยธรรมอินเดีย", "อารยธรรมจีน",
        "อารยธรรมเปอร์เซีย", "อารยธรรมอิสลาม", "มายาและแอซเท็ก",
        "ประวัติศาสตร์เอเชียตะวันออกเฉียงใต้", "ประวัติศาสตร์ไทย", "ยุคกลาง",
        "ยุคฟื้นฟูศิลปวิทยา", "การปฏิวัติทางวิทยาศาสตร์", "การปฏิวัติอุตสาหกรรม",
        "ยุคคอมพิวเตอร์", "ยุคอินเทอร์เน็ต", "ยุคปัญญาประดิษฐ์",
    ],
    "ปรัชญาและศาสตร์แห่งความคิด": [
        "Metaphysics", "Epistemology", "Logic", "Ethics", "Political Philosophy",
        "Philosophy of Science", "Philosophy of Mind", "Existentialism",
        "Rationalism", "Empiricism", "Stoicism", "Philosophy of AI",
        "Plato Aristotle Socrates", "Kant Nietzsche", "Confucius Laozi Ibn Sina",
    ],
    "คณิตศาสตร์และตรรกะ": [
        "Arithmetic", "Algebra", "Geometry", "Trigonometry", "Calculus",
        "Linear Algebra", "Differential Equations", "Discrete Mathematics",
        "Number Theory", "Set Theory", "Probability", "Statistics",
        "Optimization", "Graph Theory", "Information Theory", "Game Theory",
    ],
    "วิทยาศาสตร์ธรรมชาติ": [
        "Classical Mechanics", "Electromagnetism", "Thermodynamics",
        "Quantum Mechanics", "Relativity", "Particle Physics", "Astrophysics",
        "Cosmology", "Organic Chemistry", "Biochemistry", "Materials Chemistry",
        "Cell Biology", "Genetics", "Evolutionary Biology", "Immunology",
        "Ecology", "Geology", "Climatology", "Astronomy", "Astrobiology",
    ],
    "มนุษย์ สมอง และสติปัญญา": [
        "Neuroscience", "Cognitive Science", "Memory Science", "Learning Science",
        "Neuroplasticity", "Decision Making", "Creativity", "Consciousness",
        "Linguistics", "Anthropology", "Human Evolution", "Sleep Science",
    ],
    "ทฤษฎีสำคัญ 28 ประการ": [
        "First Principles Thinking", "Systems Thinking", "Critical Thinking",
        "Scientific Method", "Bayesian Reasoning", "Second-Order Thinking",
        "Game Theory", "Decision Theory", "Information Theory", "Complexity Theory",
        "Chaos Theory", "Cybernetics", "Network Theory", "Evolutionary Theory",
        "Control Theory", "Computational Theory", "Learning Theory",
        "Behavioral Economics", "Design Theory", "Innovation Theory", "Risk Theory",
    ],
    "วิศวกรรมศาสตร์": [
        "Mechanical Engineering", "Electrical Engineering", "Civil Engineering",
        "Chemical Engineering", "Aerospace Engineering", "Biomedical Engineering",
        "Robotics", "Control Engineering", "Telecommunications", "Systems Engineering",
    ],
    "สถาปัตยกรรมและการออกแบบ": [
        "Architectural History", "Urban Planning", "Sustainable Architecture",
        "Computational Architecture", "Biomimicry", "Smart Cities",
        "Transportation Systems", "Environmental Design", "Futuristic Architecture",
    ],
    "วิทยาการคอมพิวเตอร์และ AI": [
        "Data Structures", "Algorithms", "Operating Systems", "Database Systems",
        "Distributed Computing", "Cloud Computing", "Cybersecurity",
        "Machine Learning", "Deep Learning", "Neural Networks",
        "Reinforcement Learning", "Natural Language Processing", "Computer Vision",
        "Generative AI", "Knowledge Graphs", "AI Agents", "Explainable AI",
        "AI Safety", "AI Alignment", "AGI Research",
    ],
    "เศรษฐศาสตร์ การเมือง สังคม": [
        "Microeconomics", "Macroeconomics", "Behavioral Economics", "Finance",
        "Political Science", "International Relations", "Sociology", "Law",
        "Governance", "Geopolitics", "Strategic Management", "Social Systems",
    ],
    "ศิลปะ ภาษา ความคิดสร้างสรรค์": [
        "Art History", "Music Theory", "Graphic Design", "Film Studies",
        "Literature", "Creative Writing", "Linguistics", "Semiotics",
        "Aesthetics", "Design Thinking",
    ],
    "นวัตกรรมและการประดิษฐ์": [
        "Design Thinking", "TRIZ", "Reverse Engineering", "R&D",
        "Product Development", "Prototyping", "Experimental Design",
        "Technology Transfer", "Patent Research", "Entrepreneurship",
    ],
    "เทคโนโลยีแห่งอนาคต": [
        "AGI", "Quantum Computing", "Fusion Energy", "Humanoid Robotics",
        "Brain-Computer Interface", "Synthetic Biology", "Nanotechnology",
        "Longevity Research", "Space Colonization", "Renewable Energy",
        "Advanced Energy Storage",
    ],
    "ระเบียบวิธีวิจัย": [
        "Literature Review", "Systematic Review", "Meta-Analysis",
        "Experimental Research", "Hypothesis Testing", "Causal Inference",
        "Reproducibility", "Peer Review", "Scientific Modeling", "Simulation",
        "Evidence-Based Reasoning",
    ],
}

# Flatten into a stable ordered list of (domain, topic)
TOPICS = []
for _dom, _tops in DOMAINS.items():
    for _t in _tops:
        TOPICS.append((_dom, _t))


def total():
    return len(TOPICS)


def pick(count=1, cursor=0):
    """Return (cursor, [(domain, topic), ...]) — rotate through the master curriculum."""
    out = []
    n = total()
    if n == 0:
        return cursor, out
    for i in range(max(1, min(count, 5))):
        idx = (cursor + i) % n
        out.append(TOPICS[idx])
    return (cursor + count) % n, out


def study_prompt(domain, topic):
    """Build the 15-step study instruction for one topic (owner's directive §16)."""
    steps = "\n".join("%d) %s" % (i + 1, s) for i, s in enumerate(LEARN_STEPS))
    return ("คุณคือ Zyphere กำลังศึกษาหัวข้อ '%s' ในศาสตร์ '%s'\n"
            "จงstudyตาม 15 ขั้นตอนต่อไปนี้แบบกระชับ แล้วสรุปเป็นข้อเท็จจริงที่จำได้:\n%s\n\n"
            "กติกา: แยก ข้อเท็จจริง / สมมติฐาน / ทฤษฎี / การคาดการณ์ ออกจากกัน ชี้แหล่งที่มา "
            "และระดับความเชื่อมั่น ห้ามแต่งข้อมูลหรือแหล่งอ้างอิง ห้ามเนื้อหาผิดกฎหมายหรือเว็บพนัน") % (topic, domain, steps)
