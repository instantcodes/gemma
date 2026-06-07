"""
FastAPI Backend Server for College & Placement Assistant.
Integrates Ollama/Gemma 3, RAG, resume analysis, and placement management.
"""
import os, json, shutil, traceback
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Local modules
import database as db
import rag_engine as rag
import resume_analyzer as ra

# Try to import ollama
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

app = FastAPI(title="College & Placement Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

MODEL_NAME = "gemma3"  # Ollama model name


# ─── Pydantic Models ────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = ""
    mode: Optional[str] = "general"  # general, placement, academic, career

class StudentRequest(BaseModel):
    name: str
    roll_number: str
    department: str
    semester: Optional[int] = 1
    cgpa: Optional[float] = 0
    email: Optional[str] = ""
    phone: Optional[str] = ""
    skills: Optional[list] = []
    backlogs: Optional[int] = 0
    active_backlogs: Optional[int] = 0
    tenth_percentage: Optional[float] = 0
    twelfth_percentage: Optional[float] = 0

class CompanyRequest(BaseModel):
    name: str
    industry: Optional[str] = ""
    description: Optional[str] = ""
    website: Optional[str] = ""
    min_cgpa: Optional[float] = 0
    max_backlogs: Optional[int] = 0
    min_tenth: Optional[float] = 0
    min_twelfth: Optional[float] = 0
    required_skills: Optional[list] = []
    eligible_departments: Optional[list] = []
    package_lpa: Optional[float] = 0
    job_role: Optional[str] = ""
    job_description: Optional[str] = ""
    visit_date: Optional[str] = ""
    status: Optional[str] = "upcoming"

class InterviewPrepRequest(BaseModel):
    company: str
    role: str
    skills: Optional[list] = []
    level: Optional[str] = "fresher"


# ─── Helper: Call Gemma 3 ────────────────────────────────────────

def call_gemma(prompt: str, system_prompt: str = "") -> str:
    """Call Gemma 3 via Ollama."""
    if not OLLAMA_AVAILABLE:
        return _fallback_response(prompt)
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = ollama.chat(model=MODEL_NAME, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        print(f"Ollama error: {e}")
        return _fallback_response(prompt)


def _fallback_response(prompt: str) -> str:
    """Fallback response when Ollama is not available."""
    p = prompt.lower()
    if "placement" in p or "company" in p:
        return """Based on our college placement records:

**Placement Overview:**
- Our college maintains strong placement records with companies like TCS, Infosys, Google, Amazon, Wipro, and Zoho visiting regularly.
- The placement process typically involves aptitude tests, technical rounds, and HR interviews.

**Key Tips:**
1. Maintain a CGPA above 7.0 for most companies
2. Build strong coding and problem-solving skills
3. Participate in mock interviews and coding contests
4. Keep your resume updated with projects and internships

*Note: For more personalized responses, please ensure Ollama is running with Gemma 3 model. Run: `ollama pull gemma3` and `ollama serve`*"""

    elif "resume" in p:
        return """**Resume Tips for Engineering Students:**

1. **Header**: Clear name, contact info, LinkedIn/GitHub links
2. **Summary**: 2-3 line professional summary highlighting key strengths
3. **Education**: University, degree, CGPA, relevant coursework
4. **Skills**: Categorize into Programming, Frameworks, Tools, Soft Skills
5. **Projects**: 3-4 significant projects with tech stack and impact
6. **Experience**: Internships, part-time roles with measurable achievements
7. **Certifications**: Relevant industry certifications

*Note: Connect Ollama with Gemma 3 for AI-powered analysis.*"""

    elif "interview" in p:
        return """**Interview Preparation Guide:**

**Technical Round:**
- Data Structures & Algorithms
- DBMS concepts and SQL queries
- OOP principles
- System Design basics

**HR Round:**
- Tell me about yourself
- Why this company?
- Strengths & weaknesses
- Where do you see yourself in 5 years?

**Tips:**
- Practice on LeetCode/HackerRank
- Prepare STAR method answers
- Research the company thoroughly

*Note: Connect Ollama with Gemma 3 for personalized preparation.*"""

    else:
        return """I'm your College & Placement Assistant! I can help you with:

📚 **Academic Information** - Course details, exam schedules, regulations
💼 **Placement Support** - Company info, eligibility, preparation tips
📝 **Resume Analysis** - Upload and analyze your resume
🎯 **Interview Prep** - Practice questions and tips
🧭 **Career Guidance** - Personalized career recommendations

Please ask me any specific question, and I'll do my best to help!

*Note: For AI-powered responses using Gemma 3, ensure Ollama is running: `ollama serve`*"""


# ─── API Routes ──────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    db.init_db()
    print("✅ Database initialized")
    print(f"✅ Ollama available: {OLLAMA_AVAILABLE}")


@app.get("/api/health")
async def health():
    ollama_status = False
    if OLLAMA_AVAILABLE:
        try:
            ollama.list()
            ollama_status = True
        except:
            pass
    return {"status": "ok", "ollama": ollama_status, "documents": rag.get_doc_count()}


# ─── Chat ────────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(req: ChatRequest):
    system_prompt = """You are an AI-powered College and Placement Assistant for an engineering college.
You help students with academic queries, placement information, career guidance, interview preparation, and resume tips.
Be helpful, specific, and encouraging. Use the provided context to give accurate, data-driven answers.
Format your responses using markdown for better readability."""

    # Build context from RAG and database
    context_parts = []
    
    # Search uploaded documents
    doc_results = rag.search_documents(req.message, n_results=3)
    if doc_results:
        context_parts.append("RELEVANT DOCUMENTS:\n" + "\n---\n".join([d["content"][:500] for d in doc_results]))

    # Add database context for placement-related queries
    keywords = ["placement", "company", "student", "eligible", "package", "statistics", "placed", "cgpa", "drive"]
    if any(kw in req.message.lower() for kw in keywords):
        context_parts.append(db.get_context_for_chat())

    full_context = "\n\n".join(context_parts)
    prompt = f"""Context:\n{full_context}\n\nUser Query: {req.message}""" if full_context else req.message

    response = call_gemma(prompt, system_prompt)
    return {"response": response, "sources": [d["source"] for d in doc_results] if doc_results else []}


# ─── Documents ───────────────────────────────────────────────────

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...), doc_type: str = Form("general")):
    filepath = os.path.join(UPLOAD_DIR, file.filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    chunks = rag.add_document(filepath, file.filename, doc_type)
    conn = db.get_connection()
    conn.execute("INSERT INTO documents (filename, filepath, doc_type) VALUES (?, ?, ?)",
                 (file.filename, filepath, doc_type))
    conn.commit()
    conn.close()
    return {"message": f"Document '{file.filename}' uploaded and indexed ({chunks} chunks)", "chunks": chunks}

@app.get("/api/documents")
async def list_documents():
    conn = db.get_connection()
    rows = conn.execute("SELECT * FROM documents ORDER BY uploaded_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Students ────────────────────────────────────────────────────

@app.get("/api/students")
async def get_students():
    return db.get_all_students()

@app.get("/api/students/{roll_number}")
async def get_student(roll_number: str):
    s = db.get_student_by_roll(roll_number)
    if not s:
        raise HTTPException(404, "Student not found")
    return s

@app.post("/api/students")
async def create_student(req: StudentRequest):
    sid = db.add_student(req.dict())
    return {"id": sid, "message": "Student added successfully"}


# ─── Companies ───────────────────────────────────────────────────

@app.get("/api/companies")
async def get_companies():
    return db.get_all_companies()

@app.post("/api/companies")
async def create_company(req: CompanyRequest):
    cid = db.add_company(req.dict())
    return {"id": cid, "message": "Company added successfully"}


# ─── Placement ───────────────────────────────────────────────────

@app.get("/api/placement/stats")
async def placement_stats():
    return db.get_placement_stats()

@app.get("/api/placement/eligibility/{roll_number}")
async def check_eligibility(roll_number: str):
    student, eligible = db.check_eligibility(roll_number)
    if not student:
        raise HTTPException(404, "Student not found")
    return {"student": student, "companies": eligible}


# ─── Resume Analysis ─────────────────────────────────────────────

@app.post("/api/resume/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    filepath = os.path.join(UPLOAD_DIR, f"resume_{file.filename}")
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    text = rag.extract_text(filepath)
    if not text:
        raise HTTPException(400, "Could not extract text from resume")
    parsed = ra.parse_resume_text(text)
    parsed["raw_text"] = text
    scores = ra.score_resume(parsed)

    # Get AI feedback
    ai_prompt = f"""Analyze this resume and provide specific, actionable improvement suggestions:

Resume Content:
{text[:2000]}

Parsed Skills: {', '.join(parsed['skills'])}
Score: {scores['percentage']}/100

Provide:
1. Top 3 strengths
2. Top 3 areas for improvement
3. Specific suggestions for an engineering student seeking placements
4. ATS (Applicant Tracking System) optimization tips"""

    ai_feedback = call_gemma(ai_prompt, "You are an expert resume reviewer for engineering students.")

    return {"parsed": {k: v for k, v in parsed.items() if k != "raw_text"},
            "scores": scores, "ai_feedback": ai_feedback}


# ─── Interview Prep ──────────────────────────────────────────────

@app.post("/api/interview/prepare")
async def interview_prep(req: InterviewPrepRequest):
    prompt = f"""Generate interview preparation material for:
Company: {req.company}
Role: {req.role}
Candidate Skills: {', '.join(req.skills)}
Level: {req.level}

Provide:
1. 5 Technical questions specific to the role and skills
2. 3 Behavioral/HR questions
3. 2 Company-specific questions
4. Key topics to study
5. Tips for success at this company

Format each question with a brief expected answer approach."""

    response = call_gemma(prompt, "You are an expert interview coach for engineering placements in India.")
    return {"preparation": response, "company": req.company, "role": req.role}


# ─── Career Guidance ─────────────────────────────────────────────

@app.post("/api/career/guidance")
async def career_guidance(data: dict):
    skills = data.get("skills", [])
    interests = data.get("interests", [])
    cgpa = data.get("cgpa", 0)
    department = data.get("department", "")

    prompt = f"""Provide personalized career guidance for an engineering student:
Department: {department}
CGPA: {cgpa}
Current Skills: {', '.join(skills)}
Interests: {', '.join(interests)}

Provide:
1. Top 3 recommended career paths with reasoning
2. Skills to develop for each path
3. Recommended certifications
4. Industry trends relevant to their profile
5. Short-term (6 months) and long-term (2 years) action plan
6. Recommended companies to target"""

    response = call_gemma(prompt, "You are a career counselor specializing in engineering careers in India.")
    return {"guidance": response}


# ─── Serve Frontend ──────────────────────────────────────────────

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="frontend")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
