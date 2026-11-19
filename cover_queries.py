"""One DISTINCT real-photography search per book title.

The old design collapsed 46 books into 8 generic buckets, so many covers reused
the same photograph. This mapping gives every title its own visual subject.
Queries are English because open CC photo APIs index far more English metadata;
attribution still comes from the real source file.
"""
QUERIES = {
    "ฟิสิกส์ควอนตัม": "quantum optics laboratory laser experiment",
    "ฟิสิกส์คลาสสิก": "newton mechanics pendulum physics apparatus",
    "ดาราศาสตร์-จักรวาล": "spiral galaxy nebula deep space nasa",
    "คณิตศาสตร์บริสุทธิ์": "mathematical equations chalkboard geometry",
    "คณิตศาสตร์ประยุกต์": "engineering blueprint calculation architecture",
    "ตรรกะและทฤษฎีข้อมูล": "digital logic circuit board microchip",
    "พันธุกรรม-ชีวโมเลกุล": "dna helix",
    "เซลล์และเนื้อเยื่อ": "microscope cells laboratory",
    "ภูมิคุ้มกัน-โรค": "immunology laboratory microscope virus research",
    "สมอง-ประสาทวิทยา": "brain neuron magnetic resonance imaging",
    "สรีระและเภสัช": "human anatomy pharmacy laboratory pill",
    "การแพทย์คลินิก": "clinical hospital doctor medical equipment",
    "จิตวิทยา": "human mind psychology portrait thinking",
    "ปัญญาประดิษฐ์": "artificial intelligence server room neural network",
    "อัลกอริทึม-โครงสร้างข้อมูล": "computer programming code",
    "วิศวกรรมซอฟต์แวร์": "software development code editor programming",
    "ความมั่นคงไซเบอร์": "cybersecurity lock encryption server security",
    "ฐานข้อมูล-ข้อมูลขนาดใหญ่": "data center server racks big data",
    "คอมพิวเตอร์วิทัศน์-เสียง": "sound mixing console studio",
    "หุ่นยนต์-ระบบอัตโนมัติ": "industrial robot arm automation factory",
    "วิศวกรรมไฟฟ้า-อิเล็กทรอนิกส์": "electronic circuit board soldering components",
    "วิศวกรรมเครื่องกล": "mechanical gears engine machinery workshop",
    "วิศวกรรมโยธา-โครงสร้าง": "bridge construction steel structure crane",
    "วิศวกรรมเคมี-วัสดุ": "chemistry laboratory glassware materials science",
    "สถาปัตยกรรม-การออกแบบ": "modern architecture building design facade",
    "เศรษฐกิจมหภาค-การเงิน": "stock market financial district skyline",
    "การเงิน-การลงทุน": "investment portfolio charts trading desk",
    "การบัญชี-ตรวจสอบ": "accounting ledger audit documents calculator",
    "การตลาด-ธุรกิจ": "marketing business meeting storefront",
    "การจัดการ-ภาวะผู้นำ": "leadership team meeting office boardroom",
    "กฎหมาย-สิทธิมนุษยชน": "law justice courthouse scales statute",
    "จริยธรรม-ปรัชญา": "library books shelves",
    "ประวัติศาสตร์-อารยธรรม": "ancient civilization ruins archaeology temple",
    "สังคมวิทยา-มานุษยวิทยา": "city street people crowd",
    "รัฐศาสตร์-ความสัมพันธ์ระหว่างประเทศ": "united nations diplomacy conference world",
    "ภาษาศาสตร์-การแปล": "books languages translation dictionary typography",
    "วรรณกรรม-การเขียน": "writing author typewriter novel manuscript",
    "การสอน-การศึกษา": "classroom teacher students education chalkboard",
    "ดนตรี-เสียง": "music studio instrument sound mixing console",
    "ภาพยนตร์-สื่อ-กราฟฟิก": "film cinema camera media graphic design studio",
    "ภูมิอากาศ-สิ่งแวดล้อม": "climate forest nature environment landscape",
    "เกษตร-อาหาร": "agriculture farm field food harvest",
    "น้ำ-ทรัพยากร": "water river reservoir ocean resource",
    "พลังงาน-นิวเคลียร์": "nuclear power plant energy reactor cooling",
    "อวกาศ-การสำรวจ": "space rocket launch astronaut exploration",
    "การเอาชีวิตรอด-ความปลอดภัย": "survival wilderness safety emergency equipment",
}


def query_for(title):
    t = str(title or "").strip()
    return QUERIES.get(t) or (t + " editorial photography")
