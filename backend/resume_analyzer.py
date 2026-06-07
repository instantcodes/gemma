"""
Resume Analyzer - AI-powered resume analysis and scoring.
"""
import re
from typing import Dict, List


def parse_resume_text(text: str) -> Dict:
    """Extract structured information from resume text."""
    info = {
        "email": "", "phone": "", "skills": [], "education": [],
        "experience": [], "projects": [], "certifications": [],
        "word_count": len(text.split()), "has_summary": False
    }

    # Email
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if emails:
        info["email"] = emails[0]

    # Phone
    phones = re.findall(r'[\+]?[\d]{1,3}[-.\s]?[\d]{3,5}[-.\s]?[\d]{4,10}', text)
    if phones:
        info["phone"] = phones[0]

    # Common technical skills
    skill_keywords = [
        "python", "java", "javascript", "c++", "c#", "ruby", "go", "rust", "swift",
        "react", "angular", "vue", "node.js", "express", "django", "flask", "spring",
        "html", "css", "sql", "nosql", "mongodb", "postgresql", "mysql", "redis",
        "aws", "azure", "gcp", "docker", "kubernetes", "git", "linux",
        "machine learning", "deep learning", "ai", "nlp", "computer vision",
        "data science", "data analysis", "tensorflow", "pytorch", "pandas", "numpy",
        "agile", "scrum", "jira", "ci/cd", "rest api", "graphql", "microservices",
        "blockchain", "iot", "embedded systems", "vlsi", "matlab", "autocad",
        "figma", "photoshop", "illustrator", "excel", "power bi", "tableau"
    ]
    text_lower = text.lower()
    info["skills"] = [s for s in skill_keywords if s in text_lower]

    # Section detection
    info["has_summary"] = any(kw in text_lower for kw in ["summary", "objective", "about me", "profile"])
    info["has_education"] = any(kw in text_lower for kw in ["education", "academic", "university", "college", "degree"])
    info["has_experience"] = any(kw in text_lower for kw in ["experience", "work history", "employment"])
    info["has_projects"] = any(kw in text_lower for kw in ["project", "portfolio"])
    info["has_certifications"] = any(kw in text_lower for kw in ["certification", "certificate", "certified"])

    return info


def score_resume(parsed: Dict) -> Dict:
    """Score a resume based on completeness and quality."""
    scores = {}
    total = 0

    # Contact info (10 pts)
    contact = 0
    if parsed["email"]: contact += 5
    if parsed["phone"]: contact += 5
    scores["contact_info"] = {"score": contact, "max": 10, "feedback": "Add email and phone" if contact < 10 else "Good"}
    total += contact

    # Skills (25 pts)
    skill_count = len(parsed["skills"])
    skill_score = min(25, skill_count * 3)
    feedback = "Excellent skill set" if skill_score >= 20 else "Add more relevant technical skills" if skill_score < 10 else "Good skill coverage"
    scores["skills"] = {"score": skill_score, "max": 25, "feedback": feedback, "found": parsed["skills"]}
    total += skill_score

    # Sections (40 pts)
    section_score = 0
    section_feedback = []
    for section, label in [("has_summary","Summary/Objective"), ("has_education","Education"),
                           ("has_experience","Experience"), ("has_projects","Projects"),
                           ("has_certifications","Certifications")]:
        if parsed.get(section):
            section_score += 8
        else:
            section_feedback.append(f"Add {label} section")
    scores["sections"] = {"score": section_score, "max": 40, "feedback": "; ".join(section_feedback) if section_feedback else "All key sections present"}
    total += section_score

    # Length (15 pts)
    wc = parsed["word_count"]
    if 200 <= wc <= 800:
        length_score = 15
        lfb = "Good length"
    elif wc < 200:
        length_score = 5
        lfb = "Resume is too short, add more detail"
    elif wc <= 1200:
        length_score = 10
        lfb = "Slightly long, consider trimming"
    else:
        length_score = 5
        lfb = "Too long, keep it concise (1-2 pages)"
    scores["length"] = {"score": length_score, "max": 15, "feedback": lfb, "word_count": wc}
    total += length_score

    # Formatting (10 pts)
    fmt_score = 10
    fmt_fb = []
    if wc > 0 and text_has_all_caps_ratio(parsed.get("raw_text", "")) > 0.3:
        fmt_score -= 3
        fmt_fb.append("Reduce excessive caps")
    scores["formatting"] = {"score": fmt_score, "max": 10, "feedback": "; ".join(fmt_fb) if fmt_fb else "Acceptable formatting"}
    total += fmt_score

    return {"total_score": total, "max_score": 100, "percentage": total, "breakdown": scores,
            "grade": "A" if total >= 80 else "B" if total >= 60 else "C" if total >= 40 else "D"}


def text_has_all_caps_ratio(text: str) -> float:
    if not text:
        return 0
    words = text.split()
    caps = sum(1 for w in words if w.isupper() and len(w) > 1)
    return caps / max(len(words), 1)


def match_resume_to_job(parsed_resume: Dict, job_requirements: Dict) -> Dict:
    """Match resume skills against job requirements."""
    resume_skills = set(s.lower() for s in parsed_resume.get("skills", []))
    required = set(s.lower() for s in job_requirements.get("required_skills", []))
    preferred = set(s.lower() for s in job_requirements.get("preferred_skills", []))

    req_match = resume_skills & required
    req_missing = required - resume_skills
    pref_match = resume_skills & preferred

    req_pct = round(len(req_match) / max(len(required), 1) * 100, 1)
    overall = round((len(req_match) * 2 + len(pref_match)) / max(len(required) * 2 + len(preferred), 1) * 100, 1)

    return {
        "overall_match": overall, "required_match": req_pct,
        "matched_required": list(req_match), "missing_required": list(req_missing),
        "matched_preferred": list(pref_match),
        "recommendation": "Strong Match" if overall >= 70 else "Good Match" if overall >= 50 else "Partial Match" if overall >= 30 else "Weak Match"
    }
