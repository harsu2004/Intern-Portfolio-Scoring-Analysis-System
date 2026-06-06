import os
import re
import warnings
import logging
import requests
import joblib
import numpy as np
import pandas as pd
from pymongo import MongoClient
import certifi
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import Flask, session, render_template, request, redirect, url_for


history_collection = None
MONGO_URL = 


app = Flask(__name__)
app.secret_key = 'Team-G'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MODEL_PATH = os.path.join(BASE_DIR, "models", "readiness_regression_model.pkl")

try:
    ml_model = joblib.load(MODEL_PATH)
    print("✅ ML model loaded successfully")
except Exception as e:
    print("❌ Error loading ML model:", e)
    ml_model = None

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER



try:
    client = MongoClient(
        MONGO_URL,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=15000
    )

    client.admin.command("ping")

    print("✅ MongoDB Connected Successfully!")

    db = client["graphura"]
    history_collection = db["history"]

except Exception as e:
    print("MongoDB Connection Failed:", e)

print("ML Model Loaded Successfully!")


try:
    import pdfplumber
except ImportError:
    pdfplumber = None
    

try:
    from docx import Document
except ImportError:
    Document = None

warnings.filterwarnings("ignore")
logging.getLogger("pdfminer").setLevel(logging.ERROR)


try:
    ml_model = joblib.load("models/readiness_regression_model.pkl")
    print("ML Model Loaded Successfully!")
except Exception as e:
    print("ML Model Load Error:", e)
    ml_model = None


ROLE_SKILLS = {
    "Digital Marketing Intern": [
        "seo", "google analytics", "google ads", "meta ads",
        "email marketing", "canva", "semrush", "ahrefs",
        "content strategy", "copywriting", "campaign", "digital marketing",
    ],
    "Graphic Design Intern": [
        "photoshop", "illustrator", "indesign", "figma", "canva",
        "graphic design", "typography", "branding", "logo",
        "visual design", "mockup", "adobe",
    ],
    "Web Development Intern": [
        "html", "css", "javascript", "react", "node", "flask", "django",
        "php", "mongodb", "rest api", "git", "next.js", "express",
        "typescript", "bootstrap", "tailwind", "docker", "full stack",
    ],
    "Data Analytics Intern": [
        "python", "sql", "excel", "power bi", "tableau",
        "pandas", "numpy", "matplotlib", "scikit-learn",
        "data analysis", "data visualization", "statistics",
        "machine learning", "eda", "data cleaning", "mysql", "dashboard",
    ],
    "HR/Operations Intern": [
        "recruitment", "talent acquisition", "onboarding", "payroll",
        "employee engagement", "resume screening", "scheduling",
        "ms office", "google sheets", "performance review",
        "attendance management", "hr", "operations",
    ],
    "Content Writing Intern": [
        "content writing", "copywriting", "blogging", "seo writing",
        "proofreading", "editing", "wordpress", "research",
        "creative writing", "storytelling", "grammarly", "ms word",
    ],
    "Back End Developer Intern": [
        "python", "node", "django", "flask", "express", "php",
        "sql", "mongodb", "postgresql", "rest api", "graphql",
        "docker", "git", "authentication", "server", "database",
    ],
    "Sales & Marketing Intern": [
        "sales", "crm", "lead generation", "cold calling", "negotiation",
        "market research", "ms excel", "google sheets", "presentation",
        "client communication", "b2b", "b2c", "salesforce", "marketing",
    ],
    "UI/UX Design Intern": [
        "figma", "sketch", "adobe xd", "wireframe", "prototyping",
        "user research", "usability testing", "ui", "ux",
        "information architecture", "interaction design", "design system",
    ],
    "Front End Development Intern": [
        "html", "css", "javascript", "react", "vue", "angular",
        "typescript", "tailwind", "bootstrap", "responsive design",
        "git", "next.js", "dom", "component", "figma",
    ],
    "Social Media Management Intern": [
        "instagram", "facebook", "linkedin", "twitter", "tiktok",
        "content calendar", "canva", "hootsuite", "buffer",
        "community management", "engagement", "analytics", "reels", "social media",
    ],
    "Video Editing Intern": [
        "premiere pro", "after effects", "final cut pro", "davinci resolve",
        "video editing", "color grading", "motion graphics", "capcut",
        "storytelling", "youtube", "reels", "transitions", "audio editing",
    ],
    "Legal Internship": [
        "legal research", "contract drafting", "case study", "ms word",
        "litigation", "due diligence", "legal writing", "compliance",
        "documentation", "intellectual property", "corporate law",
        "negotiation", "legal drafting",
    ],
}


ROLE_INTERESTS = {
    "Digital Marketing Intern": [
        "marketing", "brand", "social media", "content", "digital",
        "advertising", "growth", "audience", "engagement", "media",
    ],
    "Graphic Design Intern": [
        "design", "creative", "visual", "art", "graphic", "aesthetic",
        "illustration", "animation", "branding", "portfolio",
    ],
    "Web Development Intern": [
        "coding", "programming", "software", "web", "development",
        "technology", "app", "engineer", "build", "full stack",
    ],
    "Data Analytics Intern": [
        "data", "analytics", "insights", "machine learning", "ai",
        "statistics", "research", "analysis", "modeling", "science",
    ],
    "HR/Operations Intern": [
        "people", "hr", "human resources", "recruitment", "management",
        "operations", "team", "organization", "culture", "talent",
    ],
    "Content Writing Intern": [
        "writing", "content", "storytelling", "blogging", "language",
        "creative", "research", "communication", "publishing",
    ],
    "Back End Developer Intern": [
        "coding", "backend", "server", "database", "programming",
        "api", "software", "engineering", "infrastructure",
    ],
    "Sales & Marketing Intern": [
        "sales", "marketing", "business", "growth", "client",
        "revenue", "communication", "strategy", "persuasion",
    ],
    "UI/UX Design Intern": [
        "design", "user experience", "ux", "ui", "research",
        "interaction", "visual", "product", "creative", "empathy",
    ],
    "Front End Development Intern": [
        "web", "frontend", "coding", "design", "ui",
        "javascript", "react", "visual", "programming", "browser",
    ],
    "Social Media Management Intern": [
        "social media", "content", "community", "brand", "engagement",
        "trends", "digital", "audience", "creative", "platform",
    ],
    "Video Editing Intern": [
        "video", "editing", "creative", "storytelling", "visual",
        "film", "animation", "content", "youtube", "production",
    ],
    "Legal Internship": [
        "law", "legal", "justice", "compliance", "research",
        "corporate", "policy", "drafting", "advocacy", "ethics",
    ],
}

DEGREE_WEIGHTS = {
    "phd": 100, "m.tech": 90, "mca": 90, "mba": 85, "m.sc": 85,
    "m.com": 80, "ma": 75, "b.tech": 80, "bca": 75, "bba": 70,
    "b.sc": 70, "b.com": 65, "b.voc": 65, "ba": 60, "diploma": 50,
    "12th": 30, "hsc": 30, "ssc": 20, "10th": 20,
}

def fetch_real_github_data(username):
    url = f"https://api.github.com/users/{username.strip()}/repos?sort=updated&per_page=4"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            repos = []
            for r in response.json():
                # Yahan API se real data nikal raha hai
                repos.append({
                    "name": r.get("name"),
                    "desc": r.get("description") or "No description...",
                    "lang": r.get("language") or "N/A",
                    "updated_at": r.get("updated_at"),
                    "html_url": r.get("html_url"),
                    "stars": r.get("stargazers_count", 0) # API se actual star count
                })
            return repos
    except Exception:
        pass
    return []

def extract_text(path):
    text = ""
    try:
        if path.lower().endswith(".pdf") and pdfplumber is not None:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t: text += t + " "
        elif path.lower().endswith(".docx") and Document is not None:
            doc = Document(path)
            text = "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        pass
    return text.lower().strip()

def extract_contact_info(text):
    
    cleaned_text = text.replace("\n", " ").replace(" @", "@").replace("@ ", "@")
    email = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', cleaned_text, re.IGNORECASE)
    phone = re.search(r"(\+91[\s\-]?)?[6-9]\d{4}[\s\-]?\d{5}", cleaned_text)

    return {
        "email": email.group(0) if email else "N/A",
        "phone": phone.group(0) if phone else "N/A"
    }
    
def extract_education(text):
    cgpa_match = re.search(r'(\d\.\d{1,2})[\s/]?(10|4\.0)?', text)
    edu_match = re.search(r'(education|university|college|degree)[\s\S]{0,150}', text, re.IGNORECASE)
    
    education_text = edu_match.group(0).strip() if edu_match else "N/A"
    cgpa_text = cgpa_match.group(0) if cgpa_match else "N/A"
    
    if cgpa_text != "N/A":
        return f"{education_text} (CGPA: {cgpa_text})"
    return education_text

def process_single_resume(path, target_role, input_github, fallback_name):

    text = extract_text(path)
    clean_text = text.lower()

    skills = ROLE_SKILLS.get(target_role, ROLE_SKILLS["Data Analytics Intern"])

    matched_kws = [s for s in skills if s in clean_text]
    missing_kws = [s for s in skills if s not in clean_text]

    skill_match = round((len(matched_kws) / len(skills)) * 100, 0) if skills else 0

    has_github = False
    github_username = ""

    if input_github and input_github.strip():
        has_github = True
        github_username = input_github.strip()

    elif "github" in clean_text:
        has_github = True
        github_match = re.search(r"github\.com/([a-zA-Z0-9_\-]+)", clean_text)
        github_username = github_match.group(1) if github_match else "Profile"

    missing_elements = []
    completeness = 0

    if re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", clean_text):
        completeness += 15
    else:
        missing_elements.append("Email")

    if re.search(r"\+?\d[\d \-\(\)]{8,15}\d", clean_text):
        completeness += 15
    else:
        missing_elements.append("Phone")

    completeness += min(30, int(skill_match * 0.3))

    if any(x in clean_text for x in ["education", "college", "university", "degree"]):
        completeness += 20

    if any(x in clean_text for x in ["project", "experience", "internship"]):
        completeness += 20

    contact = extract_contact_info(clean_text)
    education_info = extract_education(clean_text)

    linkedin_match = re.search(r"linkedin\.com/in/[a-zA-Z0-9_\-]+", clean_text)
    linkedin_url = "https://www." + linkedin_match.group(0) if linkedin_match else "N/A"

    session['candidate_data'] = {
        'name': fallback_name,
        'email': contact['email'],
        'phone': contact['phone'],
        'github': github_username,
        'linkedin': linkedin_url,
        "education": education_info
    }

    quality = 10

    if skill_match >= 40:
        quality += 30

    if has_github:
        quality += 20

    if re.search(r"(\b\d+%\s+|\b(optimized|built|deployed)\b)", clean_text):
        quality += 20

   
    
    kw_factor = (len(matched_kws) / len(skills)) * 45 if skills else 0

    sections_found = sum(
        1 for s in ["education", "experience", "project", "skills"]
        if s in clean_text
    )

    structure_bonus = sections_found * 5.0

    action_verbs_count = len(
        re.findall(r"\b(optimized|built|implemented|managed|designed|scaled|executed|developed|analyzed)\b", clean_text)
    )

    impact_factor = min(15, action_verbs_count * 3)

    word_count = len(clean_text.split())

    if 200 <= word_count <= 600:
        length_score = 15
    elif 601 <= word_count <= 950:
        length_score = 8
    else:
        length_score = 2

    ats_score = int(kw_factor + structure_bonus + impact_factor + length_score)
    ats_score = max(15, min(ats_score, 100))

    if sections_found < 3:
        ats_score = min(ats_score, 45)

  
    repos = fetch_real_github_data(github_username) if has_github else []
    ml_score = 0
    
    

    try:
      if ml_model:

       model_features = pd.DataFrame([{
          "skill_match": skill_match,
          "quality": quality,
          "completeness": completeness,
          "ats_score": ats_score,
          "matched_keywords": len(matched_kws),
          "word_count": word_count,
          "github": 1 if has_github else 0,

    
          "department": "Computer Science",
          "github_stars_total": 0,
          "github_repo_count": len(repos) if has_github else 0,
          "num_projects": clean_text.count("project"),
          "intern_role": target_role,
          "internship_batch": "2025",
          "tools_used_count": len(matched_kws)
    }])

       prediction = ml_model.predict(model_features)[0]

       print("Prediction:", prediction)

       ml_score = int(max(0, min(100, prediction)))

    except Exception as ml_err:
       print("ML Prediction Error:", ml_err)
    

    rule_based_score = int(
           (skill_match * 0.25) +
           (ats_score * 0.27) +
           (quality * 0.21) +
           (completeness * 0.27)
        )

    rule_based_score = max(12, min(rule_based_score, 98))


    total_score = int(
           (rule_based_score * 0.5) +
           (ml_score * 0.5)
        )

    total_score = max(12, min(total_score, 98))

    fit_label = (
          "STRONG FIT" if total_score >= 70
           else "MODERATE MATCH" if total_score >= 42
           else "NEEDS REFACTOR"
        )

    suggestions = []

    if len(missing_kws) > 0:
        suggestions.append(
            f"Explicitly mention expertise in building analytical dashboards using {', '.join([k.title() for k in missing_kws[:2]])}."
        )

    if completeness < 85:
        suggestions.append("Close system tracking gaps by indexing target words; local contact anchors detected minimal.")

    if ats_score < 60:
        suggestions.append("Enhance ATS parsing by utilizing industry-standard action verbs and bold contextual structural headers.")

    if not suggestions:
        suggestions.append("Structure alignment metrics strictly follow baseline deployment rules.")

   

    candidate_name = ""
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for line in lines[:3]:
        if any(x in line.lower() for x in ["@", "email", "phone", "github", "resume"]):
            continue
        if len(line.split()) <= 4:
            candidate_name = line.replace("(", "").replace(")", "").title()
            break

    if not candidate_name:
        candidate_name = os.path.splitext(fallback_name)[0].replace("_", " ").replace("-", " ").title()

    return {
        "name": candidate_name,
        "score": int(total_score),
        "rule_based_score": int(rule_based_score),
        "skill_match": int(skill_match),
        "quality": int(quality),
        "completeness": int(completeness),
        "ats_score": int(ats_score),
        "ml_score": int(ml_score),
        "ml_predicted_score": int(ml_score),
        "fit": fit_label,
        "matched": [s.title() for s in matched_kws],
        "missing": [s.title() for s in missing_kws],
        "sug": suggestions,
        "has_git": has_github,
        "git_user": github_username,
        "repos": repos,
        "linkedin_url": linkedin_url,
        "email": contact.get('email', 'N/A'),
        "phone": contact.get('phone', 'N/A'),
        "linkedin": linkedin_url
    }

@app.route("/")
def index():
    return render_template("index.html")


def get_candidate_info_box():
    data = session.get('candidate_data', {})
    print('KKK_III :: ', data);
    return f"""
    <div style="background: #1e293b; padding: 20px; border-radius: 12px; border-left: 5px solid #3b82f6; margin-bottom: 20px; color: white;">
        <h3 style="margin-top:0;">👤 Candidate Quick View</h3>
        <p><strong>Name:</strong> {data.get('name', 'N/A')} | <strong>Email:</strong> {data.get('email', 'N/A')} | <strong>Phone:</strong> {data.get('phone', 'N/A')}</p>
        <p><strong>Links:</strong> <a href="https://github.com/{data.get('github')}" style="color:#3b82f6;">GitHub</a> | <a href="{data.get('linkedin')}" style="color:#3b82f6;">LinkedIn</a></p>
    </div>
    """


@app.route("/analyze", methods=["POST"])
def analyze():
    mode = request.form.get("mode", "single")
    track = request.form.get("target_track", "Data Analytics Intern")
    
    if mode == "single":
        if "resume1" not in request.files: return "Error: File structural gap", 400
        f1 = request.files["resume1"]
        if f1.filename == "": return "Error: Blank streaming", 400
        git1 = request.form.get("github_user1", "").strip()
        
        p1 = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(f1.filename))
        f1.save(p1)
        r = process_single_resume(p1, track, git1, f1.filename)
        # Save to MongoDB History
        try:
            save_data = {
            "mode": "single",
            "track": track,
            "name": r['name'],
            "score": r['score'],
            "ml_score": r['ml_score'],
            "date": datetime.utcnow()
            }

            result = history_collection.insert_one(save_data)

            print("Inserted ID:", result.inserted_id)

        except Exception as db_err:
            print(f"DB Error: {db_err}")

        if os.path.exists(p1):
            os.remove(p1)
        
        
        offset_value = int(377 - (377 * r['score'] / 100))
        matched_tags = "".join([f'<span class="matrix-tag tag-match">{m}</span>' for m in r['matched']]) if r['matched'] else '<span style="color:#6b7280; font-size:0.8rem;">None detected</span>'
        missing_tags = "".join([f'<span class="matrix-tag tag-missing">{m}</span>' for m in r['missing']]) if r['missing'] else '<span style="color:#6b7280; font-size:0.8rem;">None detected</span>'
        sug_li = "".join([f'<li>{s}</li>' for s in r['sug']])
        
         
        github_section = ""
         
        if r.get('has_git'):
            github_section = f"""
            <div class="report-row-full card-bg" style="margin-top: 20px; padding: 25px;">
                <h4 style="color:#fff; margin-bottom:20px; font-size:1.1rem; display:flex; align-items:center; gap:10px;">
                    🚀 Live GitHub Repositories Crawled <span style="color:#3b82f6;">@{r['git_user']}</span>
                </h4>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; width: 100%;">
            """
            
            if r.get('repos'):
                for repo in r['repos'][:4]:
                    stars = repo.get('stars', 0)
                    github_section += f"""
                    <a href="{repo.get('html_url')}" target="_blank" style="text-decoration: none; display: block;">
                        <div style="background: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); transition: 0.3s;">
                            <div style="font-weight: 600; color: #fff; margin-bottom: 8px;">{repo.get('name')} ↗</div>
                            <div style="font-size: 0.8rem; color: #9ca3af; margin-bottom: 15px; height: 35px; overflow: hidden;">
                                {repo.get('desc', 'No description...')[:50]}...
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 0.75rem;">
                                <span style="color: #10b981;">● {repo.get('lang', 'N/A')}</span>
                                <span style="color: #fbbf24;">★ {stars}</span>
                            </div>
                        </div>
                    </a>
                    """
            github_section += "</div></div>"
       
        try:
            save_data = {
             "mode": "single",
             "track": track,
             "name": r['name'],
             "score": r['score'],
             "ml_score": r.get('ml_score', 0),
             "date": datetime.utcnow()
            }

            result = history_collection.insert_one(save_data)

            print("Inserted ID:", result.inserted_id)

        except Exception as db_err:
            print(f"DB Error: {db_err}")
            
        if os.path.exists(p1):
            os.remove(p1)
        
        return f"""
        <div class="card-bg" style="background: #131926; padding: 25px; border-radius: 12px; border-left: 5px solid #00df89; margin-bottom: 25px; color: #ffffff; border: 1px solid rgba(255,255,255,0.1); width: 100%; box-sizing: border-box;">
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 20px;">
            <div style="flex: 2;">
            <h3 style="margin: 0; font-size: 1.4rem;">Candidate Profile Summary</h3>
        </div>
        
        <div style="flex: 1; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;">
            <p style="margin: 5px 0;"><strong>Name:</strong> {r['name']}</p>
            <p style="margin: 5px 0;"><strong>Email:</strong> {r.get('email', 'N/A')}</p>
            <p style="margin: 5px 0;"><strong>Phone:</strong> {r.get('phone', 'N/A')}</p>
        </div>

        <div style="flex: 1; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 20px;">
            <p style="margin: 5px 0;"><strong>LinkedIn:</strong> 
                <a href="{r.get('linkedin', '#')}" target="_blank" style="color: #3b82f6;">View Profile</a>
            </p>
            <p style="margin: 5px 0;"><strong>GitHub:</strong> 
                
                <a href="{r.get('repos')[0].get('html_url', '#') if r.get('repos') else '#'}" target="_blank" style="color: #3b82f6;">View Profile</a>
            </p>
        </div>
    </div>
</div>

            <div id="report-anchor-target" class="main-layout-grid" style="display:grid; grid-template-columns:380px 1fr; gap:20px; align-items:start;">
                
                <div class="left-score-card card-bg">
                    <div class="profile-title">{r['name']}</div>
                    <div class="role-subtitle">{track}</div>
                    <div class="center-circle-box">
                        <div class="radial-progress-wrapper">
                            <svg class="radial-svg">
                                <circle class="circle-bg" cx="70" cy="70" r="60"></circle>
                                <circle class="circle-fill dynamic-ring-trigger"cx="70"cy="70"r="60"stroke-dasharray="377"stroke-dashoffset="377"data-offset="{offset_value}"></circle>
                            </svg>
                            <div class="circle-text-center"><div class="num">{r['score']}%</div></div>
                        </div>
                    </div>
                    <div style="width:100%; display:flex; justify-content:center;"><span class="badge-fit">{r['fit']}</span></div>
                    <div class="suggestions-box">
                        <div class="suggestions-header">Suggestions For Better Resume</div>
                        <ul class="suggestions-list">{sug_li}</ul>
                    </div>
                </div>

                <div class="right-data-column">
                    
                    <div class="card-bg" style="padding: 25px; height: fit-content;">
                        <h4 class="section-title">Core Vector Breakdown</h4>
                        <div class="metrics-list">
                            <div class="metric-row">
                                <div class="metric-info"><span>Skill Match</span><span>{r['skill_match']}%</span></div>
                                <div class="bar-container"><div class="bar-fill-track dynamic-bar-trigger" style="background-color: #3b82f6;" data-width="{r['skill_match']}%"></div></div>
                            </div>
                            <div class="metric-row">
                                <div class="metric-info"><span>Resume Quality</span><span>{r['quality']}%</span></div>
                                <div class="bar-container"><div class="bar-fill-track dynamic-bar-trigger" style="background-color: #10b981;" data-width="{r['quality']}%"></div></div>
                            </div>
                            <div class="metric-row">
                                <div class="metric-info"><span>Profile Completeness</span><span>{r['completeness']}%</span></div>
                                <div class="bar-container"><div class="bar-fill-track dynamic-bar-trigger" style="background-color: #8b5cf6;" data-width="{r['completeness']}%"></div></div>
                            </div>
                            <div class="metric-row">
                                <div class="metric-info"><span>ATS Score</span><span>{r['ats_score']}%</span></div>
                                <div class="bar-container"><div class="bar-fill-track dynamic-bar-trigger" style="background-color: #f59e0b;" data-width="{r['ats_score']}%"></div></div>
                            </div>
                            <div class="metric-row">
                                <div class="metric-info"><span>Rule Based Score</span><span>{r['rule_based_score']}%</span></div>
                                <div class="bar-container"><div class="bar-fill-track dynamic-bar-trigger"style="background-color: #06b6d4;"data-width="{r['rule_based_score']}%">
                            </div>
                        </div>
                    </div>
                            
                    
                    <div style="margin-top:15px;background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:14px;">
                       <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;text-align:center;">
                       <!-- Rule Based --><div style="flex:1;">
                       <div style="font-size:0.7rem;color:#9ca3af;margin-bottom:4px;">
                       Rule Based
                       </div>
                       <div style="font-size:1.3rem;font-weight:700;color:#06b6d4;">{r['rule_based_score']}%</div>
                    </div>
                    <!-- ML -->
                       <div style="flex:1;border-left:1px solid rgba(255,255,255,0.08);border-right:1px solid rgba(255,255,255,0.08);">
                       <div style="font-size:0.7rem;color:#9ca3af;margin-bottom:4px;">
                        ML Model
                    </div>
                        <div style=font-size:1.3rem;font-weight:700;color:#ec4899;">{r['ml_score']}%</div>
                    </div>
                    <!-- Final --><div style="flex:1;">
                        <div style="font-size:0.7rem;color:#9ca3af;margin-bottom:4px;">Final Score</div>
                    <div style="font-size:1.5rem;font-weight:800;color:#00df89;">{r['score']}%</div></div>
                    </div>
                    <div style="text-align:center;margin-top:10px;font-size:0.72rem;color:#9ca3af;">
                    Final Score = 50% ML + 50% Rule Based
                    </div>
                    </div>
                    
                    <div class="card-bg" style="padding: 25px; margin-top:20px; height: fit-content;">
                        <h4 class="section-title">Portfolio Keywords Matrix</h4>
                        <div style="margin-bottom: 18px;">
                            <div class="matrix-label-sub">Matched Keywords (Found)</div>
                            <div class="matrix-flex">{matched_tags}</div>
                        </div>
                        <div>
                            <div class="matrix-label-sub">Missing Keywords (Gaps)</div>
                            <div class="matrix-flex">{missing_tags}</div>
                        </div>
                    </div>

                </div>
            </div> {github_section}

        </div> """
        
                
    else:
       
       
        if "resume1" not in request.files or "resume2" not in request.files: 
            return "Error: Comparison mode requires 2 valid files.", 400
            
        f1 = request.files["resume1"]
        f2 = request.files["resume2"]
        if f1.filename == "" or f2.filename == "": 
            return "Error: Missing data file blocks", 400
            
        git1 = request.form.get("github_user1", "").strip()
        git2 = request.form.get("github_user2", "").strip()
        
        p1 = os.path.join(app.config["UPLOAD_FOLDER"], "alpha_" + secure_filename(f1.filename))
        p2 = os.path.join(app.config["UPLOAD_FOLDER"], "beta_" + secure_filename(f2.filename))
        f1.save(p1)
        f2.save(p2)
        
        r1 = process_single_resume(p1, track, git1, f1.filename)
        r2 = process_single_resume(p2, track, git2, f2.filename)
        
        if os.path.exists(p1): os.remove(p1)
        if os.path.exists(p2): os.remove(p2)
        
        offset1 = int(377 - (377 * r1['score'] / 100))
        offset2 = int(377 - (377 * r2['score'] / 100))
        
       
        if r1['score'] > r2['score']:
            winner_name = r1['name']
            winner_tag = "Profile Alpha"
            reason_text = f"**{r1['name']}** takes the top recommendation spot with a total readiness score of **{r1['score']}%** (versus {r2['name']}'s {r2['score']}%). This performance is backed by a superior **{r1['skill_match']}% Skill Match** matrix and enhanced structure optimization tailored closely to {track} filters."
        elif r2['score'] > r1['score']:
            winner_name = r2['name']
            winner_tag = "Profile Beta"
            reason_text = f"**{r2['name']}** secures the technical win at a **{r2['score']}%** performance index. It outpaces Alpha by matching **{r2['skill_match']}%** of the industry core skills and displaying superior document layout formatting constraints required for {track} track scanners."
        else:
            if r1['skill_match'] >= r2['skill_match']:
                winner_name = r1['name']
                winner_tag = "Profile Alpha (Tie Breaker)"
                reason_text = f"Both resumes ended in a structural tie of **{r1['score']}%**. However, **{r1['name']}** wins the spot due to stronger core alignment on technical keyword density distribution tags."
            else:
                winner_name = r2['name']
                winner_tag = "Profile Beta (Tie Breaker)"
                reason_text = f"Both resumes achieved a tie at **{r2['score']}%**. **{r2['name']}** takes the lead based on a richer technical skill checklist matching the required stack."

        verdict_html = f"""
        <div class="verdict-banner-container card-bg" id="report-anchor-target">
            <div class="verdict-badge">AI SELECTION VERDICT</div>
            <div class="verdict-main-title">🥇 Recommended Candidate: <span style="color: var(--neon-green);">{winner_name}</span> ({winner_tag})</div>
            <p class="verdict-reason-para">{reason_text}</p>
        </div>
        """
        
        try:
           save_compare = {
             "mode": "comparison",
             "track": track,
             "winner": winner_name,
             "alpha_name": r1['name'],
             "alpha_score": r1['score'],
             "beta_name": r2['name'],
             "beta_score": r2['score'],
             "date": datetime.utcnow()
           }

           result = history_collection.insert_one(save_compare)

           print("Inserted Compare ID:", result.inserted_id)

        except Exception as db_err:
           print(f"DB Error: {db_err}")
       
        
        return f"""
        {verdict_html}
        
        <div class="comparison-grid-wrapper" style="margin-top: 25px;">
            
            <div class="comparison-column-box">
                <div class="comp-header-title">Profile Alpha (Resume 1)</div>
                <div class="left-score-card card-bg" style="width:100%;">
                    <div class="profile-title">{r1['name']}</div>
                    <div class="role-subtitle">{track}</div>
                    <div class="center-circle-box">
                        <div class="radial-progress-wrapper">
                            <svg class="radial-svg">
                                <circle class="circle-bg" cx="70" cy="70" r="60"></circle>
                                <circle class="circle-fill dynamic-ring-trigger" cx="70" cy="70" r="60" stroke-dashoffset="377" data-offset="{offset1}"></circle>
                            </svg>
                            <div class="circle-text-center"><div class="num">{r1['score']}%</div></div>
                        </div>
                    </div>
                    <div style="margin-bottom:20px;"><span class="badge-fit">{r1['fit']}</span></div>
                    
                    <div class="card-bg" style="padding:25px; width:100%; text-align:left; border:1px solid rgba(255,255,255,0.02); margin-bottom:15px;">
                        <div class="matrix-label-sub">Core Vector Breakdown</div>
                        <div class="metrics-list" style="gap:12px;">
                            <div class="metric-row">
                                <div class="metric-info" style="font-size:0.75rem;"><span>Skill Match</span><span>{r1['skill_match']}%</span></div>
                                <div class="bar-container"><div class="bar-fill-track dynamic-bar-trigger" style="background-color: #3b82f6;" data-width="{r1['skill_match']}%"></div></div>
                            </div>
                            <div class="metric-row">
                                <div class="metric-info" style="font-size:0.75rem;"><span>Resume Quality</span><span>{r1['quality']}%</span></div>
                                <div class="bar-container"><div class="bar-fill-track dynamic-bar-trigger" style="background-color: #10b981;" data-width="{r1['quality']}%"></div></div>
                            </div>
                            <div class="metric-row">
                                <div class="metric-info" style="font-size:0.75rem;"><span>ATS Score</span><span>{r1['ats_score']}%</span></div>
                                <div class="bar-container"><div class="bar-fill-track dynamic-bar-trigger" style="background-color: #f59e0b;" data-width="{r1['ats_score']}%"></div></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="suggestions-box" style="margin-top:10px;">
                        <div class="suggestions-header">Alpha Keywords Detected</div>
                        <div class="matrix-flex">{"".join([f'<span class="matrix-tag tag-match">{m}</span>' for m in r1['matched'][:4]]) if r1['matched'] else '<span style="color:#6b7280; font-size:0.75rem;">None</span>'}</div>
                    </div>
                </div>
            </div>

            <div class="comparison-column-box">
                <div class="comp-header-title" style="color: var(--neon-green);">Profile Beta (Resume 2)</div>
                <div class="left-score-card card-bg" style="width:100%;">
                    <div class="profile-title">{r2['name']}</div>
                    <div class="role-subtitle">{track}</div>
                    <div class="center-circle-box">
                        <div class="radial-progress-wrapper">
                            <svg class="radial-svg">
                                <circle class="circle-bg" cx="70" cy="70" r="60"></circle>
                                <circle class="circle-fill dynamic-ring-trigger" cx="70" cy="70" r="60" stroke-dashoffset="377" data-offset="{offset2}" style="stroke: var(--neon-green);"></circle>
                            </svg>
                            <div class="circle-text-center"><div class="num">{r2['score']}%</div></div>
                        </div>
                    </div>
                    <div style="margin-bottom:20px;"><span class="badge-fit" style="color:var(--neon-green); border-color:rgba(0,223,137,0.2); background:rgba(0,223,137,0.04);">{r2['fit']}</span></div>
                    
                    <div class="card-bg" style="padding:15px; width:100%; text-align:left; border:1px solid rgba(255,255,255,0.02); margin-bottom:15px;">
                        <div class="matrix-label-sub">Core Vector Breakdown</div>
                        <div class="metrics-list" style="gap:12px;">
                            <div class="metric-row">
                                <div class="metric-info" style="font-size:0.75rem;"><span>Skill Match</span><span>{r2['skill_match']}%</span></div>
                                <div class="bar-container"><div class="bar-fill-track dynamic-bar-trigger" style="background-color: #3b82f6;" data-width="{r2['skill_match']}%"></div></div>
                            </div>
                            <div class="metric-row">
                                <div class="metric-info" style="font-size:0.75rem;"><span>Resume Quality</span><span>{r2['quality']}%</span></div>
                                <div class="bar-container"><div class="bar-fill-track dynamic-bar-trigger" style="background-color: #10b981;" data-width="{r2['quality']}%"></div></div>
                            </div>
                            <div class="metric-row">
                                <div class="metric-info" style="font-size:0.75rem;"><span>ATS Score</span><span>{r2['ats_score']}%</span></div>
                                <div class="bar-container"><div class="bar-fill-track dynamic-bar-trigger" style="background-color: #f59e0b;" data-width="{r2['ats_score']}%"></div></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="suggestions-box" style="margin-top:10px;">
                        <div class="suggestions-header">Beta Keywords Detected</div>
                        <div class="matrix-flex">{"".join([f'<span class="matrix-tag tag-match">{m}</span>' for m in r2['matched'][:4]]) if r2['matched'] else '<span style="color:#6b7280; font-size:0.75rem;">None</span>'}</div>
                    </div>
                </div>
            </div>

        </div>
        """
  

@app.route("/history")
def history_view():
    try:
        data_cursor = history_collection.find().sort("date", -1)
        records = list(data_cursor)
    except Exception as e:
        print(f"History Fetch Error: {e}")
        records = []
        
   
    html_output = """
    <div style="width: 100%; margin-top: 35px; font-family: 'Inter', system-ui, -apple-system, sans-serif; color: #ffffff;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 25px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 15px;">
            <div>
                <h4 style="color: #ffffff; margin: 0; font-size: 1.5rem; font-weight: 700; letter-spacing: -0.03em;">📊 Database Evaluation Feed</h4>
                <p style="color: #9ca3af; margin: 4px 0 0 0; font-size: 0.85rem;">Historical analysis models retrieved from MongoDB</p>
            </div>
            <div style="background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.3); color: #c084fc; padding: 6px 16px; border-radius: 50px; font-size: 0.85rem; font-weight: 600;">
                {0} Sync Matrix Active
            </div>
        </div>
        
        <div style="display: flex; flex-direction: column; gap: 15px; width: 100%;">
    """.format(len(records))
    
    for item in records:
        track_name = item.get('track', 'General Matrix')
        
      
        if item.get('mode') == 'single':
            name = item.get('name', 'Unknown Candidate')
            score = item.get('score', 0)
            
            html_output += f"""
            <div style="width: 100%; background: linear-gradient(135deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%); backdrop-filter: blur(12px); border: 1px solid rgba(139, 92, 246, 0.25); border-radius: 14px; padding: 15px 25px; box-shadow: 0 10px 20px rgba(0,0,0,0.2); position: relative; overflow: hidden; box-sizing: border-box;">
                <div style="position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: #8b5cf6;"></div>
                <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                    <div style="display: flex; align-items: center; gap: 20px;">
                        <div style="background: rgba(139, 92, 246, 0.15); color: #c084fc; padding: 4px 12px; border-radius: 50px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em; border: 1px solid rgba(139, 92, 246, 0.2); white-space: nowrap;">RESUME TYPE: SINGLE</div>
                        <h5 style="margin: 0; font-size: 1.1rem; font-weight: 600; color: #ffffff;">Name: <span style="color: #e9d5ff; font-weight: 700;">{name}</span></h5>
                        <span style="color: #6b7280; font-size: 0.8rem; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 15px;">Track: {track_name}</span>
                    </div>
                    <div>
                        <div style="background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%); color: white; padding: 6px 18px; border-radius: 8px; font-size: 1.1rem; font-weight: 800; box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);">{score}%</div>
                    </div>
                </div>
            </div>
            """
            
       
        else:
            winner = item.get('winner', 'Draw')
            alpha_name = item.get('alpha_name', 'Candidate Alpha')
            alpha_score = item.get('alpha_score', 0)
            beta_name = item.get('beta_name', 'Candidate Beta')
            beta_score = item.get('beta_score', 0)
            
            html_output += f"""
            <div style="width: 100%; background: linear-gradient(135deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%); backdrop-filter: blur(12px); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 14px; padding: 15px 25px; box-shadow: 0 10px 20px rgba(0,0,0,0.2); position: relative; overflow: hidden; box-sizing: border-box;">
                <div style="position: absolute; top: 0; left: 0; width: 8px; height: 100%; background: #10b981;"></div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; gap: 15px;">
                    <div style="display: flex; align-items: center; gap: 20px; flex-grow: 1;">
                        <div style="background: rgba(166, 185, 129, 0.15); color: #34d399; padding: 4px 12px; border-radius: 50px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em; border: 1px solid rgba(16, 185, 129, 0.2); white-space: nowrap;">RESUME INPUT: COMPARE</div>
                        
                        <div style="display: flex; align-items: center; gap: 15px; font-size: 0.9rem;">
                            <span style="color: #fff;">1st: <strong style="color:#d1d5db;">{alpha_name}</strong> ({alpha_score}%)</span>
                            <span style="color: #6b7280; font-weight: bold;">VS</span>
                            <span style="color: #fff;">2nd: <strong style="color:#d1d5db;">{beta_name}</strong> ({beta_score}%)</span>
                        </div>
                        <span style="color: #6b7280; font-size: 0.8rem; border-left: 1px solid rgba(255,255,255,0.1); padding-left: 15px; white-space: nowrap;">Track: {track_name}</span>
                    </div>
                    
                    <div style="background: rgba(16, 185, 129, 0.08); padding: 6px 18px; border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.15); white-space: nowrap;">
                        <span style="font-size: 0.9rem; color: #e5e7eb; font-weight: 500;">🏆 Who is better = </span>
                        <span style="font-size: 0.95rem; color: #34d399; font-weight: 700;">{winner}</span>
                    </div>
                </div>
            </div>
            """
            
    if not records:
        html_output += """
            <div style="text-align: center; padding: 40px; color: #4b5563; border: 2px dashed rgba(255,255,255,0.05); border-radius: 14px; width:100%; box-sizing:border-box;">
                No historical index pipelines compiled inside MongoDB yet.
            </div>
        """
        
    html_output += "</div></div>"
    return html_output
    
if __name__ == "__main__":
    app.run(debug=True, port=5000)