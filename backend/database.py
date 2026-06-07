"""
Database module for the College & Placement Assistant.
Handles SQLite operations for students, companies, and placements.
"""
import sqlite3, os, json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "college.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            roll_number TEXT UNIQUE NOT NULL, department TEXT NOT NULL,
            semester INTEGER DEFAULT 1, cgpa REAL DEFAULT 0.0,
            email TEXT, phone TEXT, skills TEXT DEFAULT '[]',
            backlogs INTEGER DEFAULT 0, active_backlogs INTEGER DEFAULT 0,
            tenth_percentage REAL DEFAULT 0.0, twelfth_percentage REAL DEFAULT 0.0,
            placement_status TEXT DEFAULT 'not_placed',
            placed_company TEXT, package_lpa REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            industry TEXT, description TEXT, website TEXT,
            min_cgpa REAL DEFAULT 0.0, max_backlogs INTEGER DEFAULT 0,
            min_tenth REAL DEFAULT 0.0, min_twelfth REAL DEFAULT 0.0,
            required_skills TEXT DEFAULT '[]', eligible_departments TEXT DEFAULT '[]',
            package_lpa REAL, job_role TEXT, job_description TEXT,
            visit_date TEXT, status TEXT DEFAULT 'upcoming',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL,
            filepath TEXT NOT NULL, doc_type TEXT DEFAULT 'general',
            description TEXT, uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    if c.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        _insert_sample_data(c)
    conn.commit()
    conn.close()

def _insert_sample_data(c):
    students = [
        ("Arun Kumar","CS2021001","Computer Science",7,8.5,"arun@college.edu","9876543210",
         json.dumps(["Python","Java","Machine Learning","SQL"]),0,0,92.0,88.0,"placed","TCS",7.0),
        ("Priya Sharma","CS2021002","Computer Science",7,9.1,"priya@college.edu","9876543211",
         json.dumps(["Python","React","Node.js","MongoDB"]),0,0,95.0,91.0,"placed","Infosys",8.5),
        ("Rahul Nair","EC2021001","Electronics",7,7.8,"rahul@college.edu","9876543212",
         json.dumps(["VLSI","Embedded Systems","C","Python"]),1,0,85.0,80.0,"not_placed",None,None),
        ("Sneha Menon","CS2021003","Computer Science",7,8.9,"sneha@college.edu","9876543213",
         json.dumps(["Java","Spring Boot","AWS","Docker"]),0,0,90.0,87.0,"not_placed",None,None),
        ("Vishnu Prasad","ME2021001","Mechanical",7,7.2,"vishnu@college.edu","9876543214",
         json.dumps(["AutoCAD","SolidWorks","MATLAB"]),2,1,78.0,72.0,"not_placed",None,None),
        ("Anjali Das","CS2021004","Computer Science",5,8.7,"anjali@college.edu","9876543215",
         json.dumps(["Python","Data Science","TensorFlow","SQL"]),0,0,94.0,90.0,"not_placed",None,None),
        ("Mohammed Faisal","IT2021001","Information Technology",7,8.0,"faisal@college.edu","9876543216",
         json.dumps(["JavaScript","React","Node.js","PostgreSQL"]),0,0,88.0,83.0,"not_placed",None,None),
        ("Kavya Nair","IT2021002","Information Technology",7,9.3,"kavya@college.edu","9876543219",
         json.dumps(["Python","AI","Deep Learning","NLP","Cloud Computing"]),0,0,96.0,94.0,"placed","Google",25.0),
    ]
    for s in students:
        c.execute("INSERT INTO students (name,roll_number,department,semester,cgpa,email,phone,skills,backlogs,active_backlogs,tenth_percentage,twelfth_percentage,placement_status,placed_company,package_lpa) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", s)

    companies = [
        ("TCS","IT Services","Tata Consultancy Services","https://tcs.com",6.0,0,60.0,60.0,
         json.dumps(["Java","Python","SQL"]),json.dumps(["Computer Science","Information Technology","Electronics"]),
         7.0,"Software Developer","Full stack development","2026-01-15","completed"),
        ("Infosys","IT Services","Infosys - Digital services leader","https://infosys.com",7.0,0,65.0,65.0,
         json.dumps(["Java","Python","React","SQL"]),json.dumps(["Computer Science","Information Technology"]),
         8.5,"Systems Engineer","Enterprise application development","2026-02-10","completed"),
        ("Google","Technology","Google LLC","https://google.com",8.5,0,85.0,85.0,
         json.dumps(["Python","AI","Machine Learning","Algorithms"]),json.dumps(["Computer Science"]),
         25.0,"Software Engineer","Large-scale distributed systems","2026-03-05","completed"),
        ("Wipro","IT Services","Wipro Limited","https://wipro.com",6.0,1,55.0,55.0,
         json.dumps(["Java","Python","Testing"]),json.dumps(["Computer Science","Information Technology","Electronics","Mechanical"]),
         5.5,"Project Engineer","Software development and testing","2026-04-20","upcoming"),
        ("Amazon","E-Commerce/Technology","Amazon Web Services","https://amazon.com",7.5,0,70.0,70.0,
         json.dumps(["Java","Python","AWS","System Design"]),json.dumps(["Computer Science","Information Technology"]),
         18.0,"SDE-1","Scalable backend systems","2026-05-15","upcoming"),
        ("Zoho","Software","Zoho Corporation","https://zoho.com",7.0,0,70.0,70.0,
         json.dumps(["Java","JavaScript","SQL"]),json.dumps(["Computer Science","Information Technology"]),
         10.0,"Member Technical Staff","Product development","2026-06-01","upcoming"),
    ]
    for co in companies:
        c.execute("INSERT INTO companies (name,industry,description,website,min_cgpa,max_backlogs,min_tenth,min_twelfth,required_skills,eligible_departments,package_lpa,job_role,job_description,visit_date,status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", co)

def get_all_students():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM students ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_student_by_roll(roll_number):
    conn = get_connection()
    row = conn.execute("SELECT * FROM students WHERE roll_number = ?", (roll_number,)).fetchone()
    conn.close()
    return dict(row) if row else None

def add_student(data):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO students (name,roll_number,department,semester,cgpa,email,phone,skills,backlogs,active_backlogs,tenth_percentage,twelfth_percentage) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (data["name"],data["roll_number"],data["department"],data.get("semester",1),data.get("cgpa",0),
         data.get("email",""),data.get("phone",""),json.dumps(data.get("skills",[])),
         data.get("backlogs",0),data.get("active_backlogs",0),data.get("tenth_percentage",0),data.get("twelfth_percentage",0)))
    conn.commit()
    sid = c.lastrowid
    conn.close()
    return sid

def get_all_companies():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM companies ORDER BY visit_date DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_company_by_id(cid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM companies WHERE id = ?", (cid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def add_company(data):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO companies (name,industry,description,website,min_cgpa,max_backlogs,min_tenth,min_twelfth,required_skills,eligible_departments,package_lpa,job_role,job_description,visit_date,status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (data["name"],data.get("industry",""),data.get("description",""),data.get("website",""),
         data.get("min_cgpa",0),data.get("max_backlogs",0),data.get("min_tenth",0),data.get("min_twelfth",0),
         json.dumps(data.get("required_skills",[])),json.dumps(data.get("eligible_departments",[])),
         data.get("package_lpa",0),data.get("job_role",""),data.get("job_description",""),
         data.get("visit_date",""),data.get("status","upcoming")))
    conn.commit()
    cid = c.lastrowid
    conn.close()
    return cid

def get_placement_stats():
    conn = get_connection()
    s = {}
    s["total_students"] = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    s["placed_students"] = conn.execute("SELECT COUNT(*) FROM students WHERE placement_status='placed'").fetchone()[0]
    s["total_companies"] = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    s["upcoming_drives"] = conn.execute("SELECT COUNT(*) FROM companies WHERE status='upcoming'").fetchone()[0]
    s["avg_package"] = round(conn.execute("SELECT COALESCE(AVG(package_lpa),0) FROM students WHERE placement_status='placed'").fetchone()[0], 2)
    s["highest_package"] = conn.execute("SELECT COALESCE(MAX(package_lpa),0) FROM students WHERE placement_status='placed'").fetchone()[0]
    dept = conn.execute("SELECT department, COUNT(*) as total, SUM(CASE WHEN placement_status='placed' THEN 1 ELSE 0 END) as placed FROM students GROUP BY department").fetchall()
    s["department_stats"] = [dict(d) for d in dept]
    conn.close()
    return s

def check_eligibility(student_roll):
    student = get_student_by_roll(student_roll)
    if not student:
        return None, []
    companies = get_all_companies()
    eligible = []
    for co in companies:
        reasons = []
        ok = True
        if student["cgpa"] < co["min_cgpa"]:
            reasons.append(f"CGPA {student['cgpa']} < required {co['min_cgpa']}")
            ok = False
        if student["active_backlogs"] > co["max_backlogs"]:
            reasons.append(f"Active backlogs {student['active_backlogs']} > allowed {co['max_backlogs']}")
            ok = False
        if student["tenth_percentage"] < co["min_tenth"]:
            reasons.append(f"10th% {student['tenth_percentage']} < required {co['min_tenth']}")
            ok = False
        if student["twelfth_percentage"] < co["min_twelfth"]:
            reasons.append(f"12th% {student['twelfth_percentage']} < required {co['min_twelfth']}")
            ok = False
        edepts = json.loads(co["eligible_departments"]) if co["eligible_departments"] else []
        if edepts and student["department"] not in edepts:
            reasons.append(f"Department '{student['department']}' not eligible")
            ok = False
        sskills = set(x.lower() for x in json.loads(student["skills"]))
        rskills = set(x.lower() for x in (json.loads(co["required_skills"]) if co["required_skills"] else []))
        match = sskills & rskills
        missing = rskills - sskills
        pct = round(len(match)/max(len(rskills),1)*100, 1)
        eligible.append({"company":co["name"],"company_id":co["id"],"job_role":co["job_role"],
            "package_lpa":co["package_lpa"],"visit_date":co["visit_date"],"status":co["status"],
            "is_eligible":ok,"reasons":reasons,"skill_match_pct":pct,
            "matching_skills":list(match),"missing_skills":list(missing)})
    eligible.sort(key=lambda x: (-x["is_eligible"], -x["package_lpa"]))
    return student, eligible

def get_context_for_chat():
    stats = get_placement_stats()
    companies = get_all_companies()
    students = get_all_students()
    ctx = f"""COLLEGE PLACEMENT DATABASE:
Stats: {stats['total_students']} students, {stats['placed_students']} placed ({round(stats['placed_students']/max(stats['total_students'],1)*100,1)}%), {stats['total_companies']} companies, Avg pkg: {stats['avg_package']} LPA, Highest: {stats['highest_package']} LPA
"""
    ctx += "\nDepartment Stats:\n"
    for d in stats["department_stats"]:
        ctx += f"- {d['department']}: {d['placed']}/{d['total']} placed\n"
    ctx += "\nCompanies:\n"
    for co in companies:
        ctx += f"- {co['name']}: {co['job_role']}, {co['package_lpa']} LPA, Min CGPA: {co['min_cgpa']}, Status: {co['status']}\n"
    ctx += "\nStudents:\n"
    for s in students:
        ctx += f"- {s['name']} ({s['roll_number']}): {s['department']}, CGPA: {s['cgpa']}, {s['placement_status']}"
        if s['placed_company']:
            ctx += f" at {s['placed_company']} ({s['package_lpa']} LPA)"
        ctx += "\n"
    return ctx

if __name__ == "__main__":
    init_db()
    print("Database initialized with sample data.")
