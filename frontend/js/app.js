const API = 'http://localhost:8000/api';
let backendOnline = false;

// ── Navigation ──
function navigateTo(page) {
  document.querySelectorAll('.page-section').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const el = document.getElementById('page-' + page);
  const nav = document.getElementById('nav-' + page);
  if (el) el.classList.add('active');
  if (nav) nav.classList.add('active');
  if (page === 'dashboard') loadDashboard();
  if (page === 'students') loadStudents();
  if (page === 'companies') loadCompanies();
  if (page === 'documents') loadDocuments();
}

document.querySelectorAll('.nav-item[data-page]').forEach(item => {
  item.addEventListener('click', () => navigateTo(item.dataset.page));
});

// ── Sidebar Toggle ──
document.getElementById('sidebarToggle').addEventListener('click', () => {
  document.getElementById('sidebar').classList.toggle('collapsed');
});

// ── Modals ──
function openModal(id) { document.getElementById(id).classList.add('active'); }
function closeModal(id) { document.getElementById(id).classList.remove('active'); }

// ── API Helper ──
async function api(path, opts = {}) {
  try {
    const r = await fetch(API + path, opts);
    if (!r.ok) throw new Error(r.statusText);
    return await r.json();
  } catch (e) {
    console.warn('API error:', e);
    return null;
  }
}

// ── Health Check ──
async function checkHealth() {
  const dot = document.getElementById('aiStatus');
  const txt = document.getElementById('aiStatusText');
  const data = await api('/health');
  if (data) {
    backendOnline = true;
    dot.className = 'status-dot ' + (data.ollama ? 'online' : 'offline');
    txt.textContent = data.ollama ? 'Gemma 3 Online' : 'Backend OK (No Ollama)';
  } else {
    dot.className = 'status-dot offline';
    txt.textContent = 'Backend Offline';
  }
}

// ── Dashboard ──
const SAMPLE_STATS = {
  total_students: 8, placed_students: 3, total_companies: 6,
  upcoming_drives: 3, avg_package: 13.5, highest_package: 25.0,
  department_stats: [
    { department: 'Computer Science', total: 5, placed: 2 },
    { department: 'Electronics', total: 1, placed: 0 },
    { department: 'Information Technology', total: 2, placed: 1 }
  ]
};
const SAMPLE_COMPANIES = [
  { name: 'Wipro', job_role: 'Project Engineer', package_lpa: 5.5, visit_date: '2026-04-20', status: 'upcoming' },
  { name: 'Amazon', job_role: 'SDE-1', package_lpa: 18.0, visit_date: '2026-05-15', status: 'upcoming' },
  { name: 'Zoho', job_role: 'Member Technical Staff', package_lpa: 10.0, visit_date: '2026-06-01', status: 'upcoming' }
];

async function loadDashboard() {
  let stats = await api('/placement/stats');
  if (!stats) stats = SAMPLE_STATS;
  document.getElementById('statStudents').textContent = stats.total_students;
  document.getElementById('statPlaced').textContent = stats.placed_students;
  document.getElementById('statCompanies').textContent = stats.total_companies;
  document.getElementById('statPackage').textContent = stats.highest_package;

  let deptHtml = '';
  (stats.department_stats || []).forEach(d => {
    const pct = d.total ? Math.round(d.placed / d.total * 100) : 0;
    deptHtml += `<div style="margin-bottom:14px"><div style="display:flex;justify-content:space-between;margin-bottom:4px"><span style="font-size:13px">${d.department}</span><span style="font-size:12px;color:var(--text-muted)">${d.placed}/${d.total} (${pct}%)</span></div><div class="progress-bar"><div class="progress-fill ${pct>=60?'good':pct>=30?'medium':'low'}" style="width:${pct}%"></div></div></div>`;
  });
  document.getElementById('deptStats').innerHTML = deptHtml || '<p style="color:var(--text-muted)">No data</p>';

  let companies = await api('/companies');
  if (!companies) companies = SAMPLE_COMPANIES;
  const upcoming = companies.filter(c => c.status === 'upcoming');
  let driveHtml = '';
  upcoming.forEach(c => {
    driveHtml += `<div class="elig-card eligible" style="border-left-color:var(--accent)"><div style="display:flex;justify-content:space-between;align-items:center"><div><strong style="font-size:14px">${c.name}</strong><p style="font-size:12px;color:var(--text-muted)">${c.job_role} • ${c.package_lpa} LPA</p></div><span class="badge badge-info">${c.visit_date}</span></div></div>`;
  });
  document.getElementById('upcomingDrives').innerHTML = driveHtml || '<p style="color:var(--text-muted)">No upcoming drives</p>';
}

// ── Chat ──
function clearChat() {
  const el = document.getElementById('chatMessages');
  el.innerHTML = `<div class="chat-message assistant"><div class="avatar">🎓</div><div class="chat-bubble"><p><strong>Chat cleared.</strong> How can I help you?</p></div></div>`;
}

function addChatMessage(role, content) {
  const el = document.getElementById('chatMessages');
  const icon = role === 'user' ? '👤' : '🎓';
  const html = formatMarkdown(content);
  el.innerHTML += `<div class="chat-message ${role}"><div class="avatar">${icon}</div><div class="chat-bubble">${html}</div></div>`;
  el.scrollTop = el.scrollHeight;
}

function showTyping() {
  const el = document.getElementById('chatMessages');
  el.innerHTML += `<div class="chat-message assistant" id="typingMsg"><div class="avatar">🎓</div><div class="chat-bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div></div>`;
  el.scrollTop = el.scrollHeight;
}
function removeTyping() { const t = document.getElementById('typingMsg'); if (t) t.remove(); }

async function sendChat() {
  const input = document.getElementById('chatInput');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';
  addChatMessage('user', msg);
  showTyping();

  const data = await api('/chat', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: msg })
  });
  removeTyping();

  if (data && data.response) {
    addChatMessage('assistant', data.response);
  } else {
    addChatMessage('assistant', getFallbackResponse(msg));
  }
}

function getFallbackResponse(msg) {
  const m = msg.toLowerCase();
  if (m.includes('placement') || m.includes('company'))
    return "**Placement Information:**\n\nOur college has partnerships with companies like TCS, Infosys, Google, Amazon, Wipro, and Zoho.\n\n**Key Requirements:**\n- Most companies require CGPA ≥ 6.0-7.0\n- No active backlogs for top companies\n- Strong coding skills in at least 2 languages\n\n*Connect the backend with Ollama for detailed AI responses.*";
  if (m.includes('resume'))
    return "**Resume Tips:**\n\n1. Keep it to 1-2 pages\n2. Include: Contact, Summary, Education, Skills, Projects, Experience\n3. Use action verbs and quantify achievements\n4. Tailor for each application\n\nUse the **Resume Analyzer** tab for detailed AI feedback!";
  if (m.includes('interview'))
    return "**Interview Prep Tips:**\n\n1. Practice DSA on LeetCode/HackerRank\n2. Review core CS concepts (DBMS, OS, Networks)\n3. Prepare behavioral answers using STAR method\n4. Research the company thoroughly\n\nUse the **Interview Prep** tab for AI-generated questions!";
  return "I'm your College & Placement Assistant! I can help with:\n\n- 📚 Academic queries\n- 💼 Placement info\n- 📝 Resume analysis\n- 🎯 Interview prep\n- 🧭 Career guidance\n\n*Start the backend server for full AI capabilities: `python backend/main.py`*";
}

document.getElementById('chatInput').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
});

// ── Documents ──
async function loadDocuments() {
  const data = await api('/documents');
  const list = document.getElementById('docList');
  const count = document.getElementById('docCount');
  if (data && data.length > 0) {
    count.textContent = data.length;
    list.innerHTML = data.map(d => `<div class="elig-card eligible" style="border-left-color:var(--info)"><div style="display:flex;justify-content:space-between;align-items:center"><div><strong>${d.filename}</strong><p style="font-size:12px;color:var(--text-muted)">${d.doc_type} • ${d.uploaded_at || 'recently'}</p></div><span class="badge badge-accent">${d.doc_type}</span></div></div>`).join('');
  }
}

const docArea = document.getElementById('docUploadArea');
const docInput = document.getElementById('docFileInput');
docArea.addEventListener('click', () => docInput.click());
docArea.addEventListener('dragover', e => { e.preventDefault(); docArea.classList.add('dragover'); });
docArea.addEventListener('dragleave', () => docArea.classList.remove('dragover'));
docArea.addEventListener('drop', e => { e.preventDefault(); docArea.classList.remove('dragover'); uploadDocs(e.dataTransfer.files); });
docInput.addEventListener('change', () => uploadDocs(docInput.files));

async function uploadDocs(files) {
  const prog = document.getElementById('uploadProgress');
  const bar = document.getElementById('uploadBar');
  const status = document.getElementById('uploadStatus');
  prog.style.display = 'block';
  for (let i = 0; i < files.length; i++) {
    status.textContent = `Uploading ${files[i].name}...`;
    bar.style.width = ((i + 1) / files.length * 100) + '%';
    const fd = new FormData();
    fd.append('file', files[i]);
    fd.append('doc_type', 'general');
    await api('/documents/upload', { method: 'POST', body: fd });
  }
  status.textContent = 'Upload complete!';
  setTimeout(() => { prog.style.display = 'none'; }, 2000);
  loadDocuments();
}

// ── Resume Analyzer ──
const resumeArea = document.getElementById('resumeUploadArea');
const resumeInput = document.getElementById('resumeFileInput');
resumeArea.addEventListener('click', () => resumeInput.click());
resumeInput.addEventListener('change', () => analyzeResume(resumeInput.files[0]));

async function analyzeResume(file) {
  if (!file) return;
  resumeArea.style.display = 'none';
  document.getElementById('resumeAnalyzing').style.display = 'block';

  const fd = new FormData();
  fd.append('file', file);
  const data = await api('/resume/analyze', { method: 'POST', body: fd });

  document.getElementById('resumeAnalyzing').style.display = 'none';
  resumeArea.style.display = '';

  if (!data) { alert('Resume analysis requires the backend server. Run: python backend/main.py'); return; }

  const results = document.getElementById('resumeResults');
  results.style.display = '';
  const s = data.scores;
  let html = `<div style="text-align:center;margin-bottom:20px"><div class="score-circle" style="--score:${s.percentage}"><span>${s.percentage}</span></div><p style="font-size:18px;font-weight:700">Grade: ${s.grade}</p></div>`;
  for (const [key, val] of Object.entries(s.breakdown)) {
    const pct = Math.round(val.score / val.max * 100);
    html += `<div style="margin-bottom:12px"><div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px"><span>${key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</span><span>${val.score}/${val.max}</span></div><div class="progress-bar"><div class="progress-fill ${pct>=70?'good':pct>=40?'medium':'low'}" style="width:${pct}%"></div></div><p style="font-size:11px;color:var(--text-muted);margin-top:2px">${val.feedback}</p></div>`;
  }
  if (data.parsed && data.parsed.skills && data.parsed.skills.length) {
    html += `<div style="margin-top:16px"><p style="font-size:13px;font-weight:600;margin-bottom:8px">Skills Found:</p><div class="tag-list">${data.parsed.skills.map(s => `<span class="tag">${s}</span>`).join('')}</div></div>`;
  }
  document.getElementById('resumeScoreArea').innerHTML = html;

  if (data.ai_feedback) {
    const fb = document.getElementById('resumeAIFeedback');
    fb.style.display = '';
    document.getElementById('aiFeedbackContent').innerHTML = formatMarkdown(data.ai_feedback);
  }
}

// ── Eligibility ──
async function checkEligibility() {
  const roll = document.getElementById('eligRollInput').value.trim();
  if (!roll) return;
  const btn = document.getElementById('eligCheckBtn');
  btn.innerHTML = '<span class="spinner"></span> Checking...';

  let data = await api('/placement/eligibility/' + roll);
  btn.textContent = 'Check Eligibility';

  if (!data) {
    // Fallback demo data
    data = getDemoEligibility(roll);
    if (!data) { document.getElementById('eligResults').innerHTML = '<div class="card"><p style="color:var(--danger)">Student not found. Try: CS2021001, CS2021003, IT2021001</p></div>'; return; }
  }

  const s = data.student;
  let html = `<div class="card" style="margin-bottom:16px"><div style="display:flex;justify-content:space-between;align-items:center"><div><h3 style="font-size:18px">${s.name}</h3><p style="color:var(--text-muted);font-size:13px">${s.roll_number} • ${s.department} • CGPA: ${s.cgpa}</p></div><span class="badge ${s.placement_status==='placed'?'badge-success':'badge-warning'}">${s.placement_status==='placed'?'Placed':'Not Placed'}</span></div></div>`;

  data.companies.forEach(c => {
    html += `<div class="elig-card ${c.is_eligible?'eligible':'not-eligible'}"><div style="display:flex;justify-content:space-between;align-items:start"><div><strong>${c.company}</strong> — ${c.job_role}<p style="font-size:12px;color:var(--text-muted)">${c.package_lpa} LPA • ${c.visit_date} • ${c.status}</p></div><span class="badge ${c.is_eligible?'badge-success':'badge-danger'}">${c.is_eligible?'Eligible':'Not Eligible'}</span></div>`;
    if (c.skill_match_pct !== undefined) html += `<div style="margin-top:8px"><div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px"><span>Skill Match</span><span>${c.skill_match_pct}%</span></div><div class="progress-bar"><div class="progress-fill ${c.skill_match_pct>=70?'good':c.skill_match_pct>=40?'medium':'low'}" style="width:${c.skill_match_pct}%"></div></div></div>`;
    if (!c.is_eligible && c.reasons.length) html += `<div style="margin-top:6px">${c.reasons.map(r => `<p style="font-size:11px;color:var(--danger)">⚠ ${r}</p>`).join('')}</div>`;
    if (c.missing_skills && c.missing_skills.length) html += `<div style="margin-top:6px"><span style="font-size:11px;color:var(--text-muted)">Missing: </span><span class="tag-list" style="display:inline">${c.missing_skills.map(s=>`<span class="tag" style="background:rgba(239,68,68,0.1);color:var(--danger);border-color:rgba(239,68,68,0.2)">${s}</span>`).join(' ')}</span></div>`;
    html += '</div>';
  });
  document.getElementById('eligResults').innerHTML = html;
}

function getDemoEligibility(roll) {
  const demos = {
    'CS2021001': { student: { name:'Arun Kumar', roll_number:'CS2021001', department:'Computer Science', cgpa:8.5, placement_status:'placed' }, companies: [
      { company:'TCS', job_role:'Software Developer', package_lpa:7, visit_date:'2026-01-15', status:'completed', is_eligible:true, reasons:[], skill_match_pct:100, missing_skills:[] },
      { company:'Infosys', job_role:'Systems Engineer', package_lpa:8.5, visit_date:'2026-02-10', status:'completed', is_eligible:true, reasons:[], skill_match_pct:75, missing_skills:['react'] },
      { company:'Google', job_role:'Software Engineer', package_lpa:25, visit_date:'2026-03-05', status:'completed', is_eligible:true, reasons:[], skill_match_pct:75, missing_skills:['algorithms'] },
      { company:'Amazon', job_role:'SDE-1', package_lpa:18, visit_date:'2026-05-15', status:'upcoming', is_eligible:true, reasons:[], skill_match_pct:50, missing_skills:['aws','system design'] }
    ]},
    'CS2021003': { student: { name:'Sneha Menon', roll_number:'CS2021003', department:'Computer Science', cgpa:8.9, placement_status:'not_placed' }, companies: [
      { company:'TCS', job_role:'Software Developer', package_lpa:7, visit_date:'2026-01-15', status:'completed', is_eligible:true, reasons:[], skill_match_pct:66, missing_skills:['python'] },
      { company:'Amazon', job_role:'SDE-1', package_lpa:18, visit_date:'2026-05-15', status:'upcoming', is_eligible:true, reasons:[], skill_match_pct:75, missing_skills:['system design'] }
    ]}
  };
  return demos[roll] || null;
}

// ── Interview Prep ──
async function generateInterview() {
  const btn = document.getElementById('intGenBtn');
  btn.innerHTML = '<span class="spinner"></span> Generating...';
  const body = {
    company: document.getElementById('intCompany').value || 'TCS',
    role: document.getElementById('intRole').value || 'Software Developer',
    skills: (document.getElementById('intSkills').value || 'Python,Java').split(',').map(s => s.trim()),
    level: document.getElementById('intLevel').value
  };
  const data = await api('/interview/prepare', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
  btn.textContent = '🎯 Generate Questions';
  const res = document.getElementById('intResults');
  res.style.display = '';
  if (data && data.preparation) {
    document.getElementById('intContent').innerHTML = formatMarkdown(data.preparation);
  } else {
    document.getElementById('intContent').innerHTML = formatMarkdown(getInterviewFallback(body));
  }
}

function getInterviewFallback(b) {
  return `# Interview Prep: ${b.company} — ${b.role}\n\n## Technical Questions\n1. **Explain OOP concepts** with real-world examples\n2. **What is the difference between** an abstract class and interface?\n3. **Write a program** to find the second largest element in an array\n4. **Explain normalization** in DBMS (1NF, 2NF, 3NF)\n5. **What are ${b.skills.slice(0,2).join(' and ')}** used for in industry?\n\n## Behavioral Questions\n1. Tell me about yourself\n2. Describe a challenging project you worked on\n3. Where do you see yourself in 5 years?\n\n## Tips\n- Research ${b.company}'s recent projects and values\n- Practice coding problems daily\n- Prepare STAR method answers for behavioral rounds\n- Be confident and ask thoughtful questions\n\n*Start the backend with Gemma 3 for personalized AI-generated questions!*`;
}

// ── Career Guidance ──
async function getCareerGuidance() {
  const btn = document.getElementById('careerBtn');
  btn.innerHTML = '<span class="spinner"></span> Analyzing...';
  const body = {
    department: document.getElementById('careerDept').value,
    cgpa: parseFloat(document.getElementById('careerCgpa').value) || 8,
    skills: (document.getElementById('careerSkills').value || '').split(',').map(s => s.trim()).filter(Boolean),
    interests: (document.getElementById('careerInterests').value || '').split(',').map(s => s.trim()).filter(Boolean)
  };
  const data = await api('/career/guidance', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
  btn.textContent = '🧭 Get Career Guidance';
  const res = document.getElementById('careerResults');
  res.style.display = '';
  if (data && data.guidance) {
    document.getElementById('careerContent').innerHTML = formatMarkdown(data.guidance);
  } else {
    document.getElementById('careerContent').innerHTML = formatMarkdown(getCareerFallback(body));
  }
}

function getCareerFallback(b) {
  return `# Career Guidance for ${b.department} Student\n\n## Recommended Career Paths\n1. **Software Development** — High demand, great packages\n2. **Data Science / AI** — Growing field with lucrative opportunities\n3. **Cloud & DevOps Engineering** — Essential for modern infrastructure\n\n## Skills to Develop\n- Data Structures & Algorithms\n- System Design\n- Cloud platforms (AWS/Azure/GCP)\n- At least one scripting language (Python recommended)\n\n## Certifications\n- AWS Cloud Practitioner\n- Google IT Automation with Python\n- Microsoft Azure Fundamentals\n\n## Action Plan\n**Next 6 months:** Build 3 solid projects, contribute to open source, practice DSA daily\n**Next 2 years:** Target product-based companies, build expertise in a niche\n\n*Connect Gemma 3 for personalized AI guidance!*`;
}

// ── Students & Companies Tables ──
async function loadStudents() {
  let data = await api('/students');
  if (!data) data = [
    { name:'Arun Kumar', roll_number:'CS2021001', department:'Computer Science', cgpa:8.5, placement_status:'placed', placed_company:'TCS', package_lpa:7 },
    { name:'Priya Sharma', roll_number:'CS2021002', department:'Computer Science', cgpa:9.1, placement_status:'placed', placed_company:'Infosys', package_lpa:8.5 },
    { name:'Sneha Menon', roll_number:'CS2021003', department:'Computer Science', cgpa:8.9, placement_status:'not_placed' },
    { name:'Kavya Nair', roll_number:'IT2021002', department:'Information Technology', cgpa:9.3, placement_status:'placed', placed_company:'Google', package_lpa:25 }
  ];
  let html = '<table class="data-table"><thead><tr><th>Name</th><th>Roll No</th><th>Dept</th><th>CGPA</th><th>Status</th><th>Company</th></tr></thead><tbody>';
  data.forEach(s => {
    html += `<tr><td>${s.name}</td><td>${s.roll_number}</td><td>${s.department}</td><td>${s.cgpa}</td><td><span class="badge ${s.placement_status==='placed'?'badge-success':'badge-warning'}">${s.placement_status==='placed'?'Placed':'Open'}</span></td><td>${s.placed_company||'—'}${s.package_lpa?' ('+s.package_lpa+' LPA)':''}</td></tr>`;
  });
  html += '</tbody></table>';
  document.getElementById('studentsTable').innerHTML = html;
}

async function loadCompanies() {
  let data = await api('/companies');
  if (!data) data = SAMPLE_COMPANIES;
  let html = '<table class="data-table"><thead><tr><th>Company</th><th>Role</th><th>Package</th><th>Visit Date</th><th>Status</th></tr></thead><tbody>';
  data.forEach(c => {
    const badge = c.status==='completed'?'badge-success':c.status==='upcoming'?'badge-info':'badge-warning';
    html += `<tr><td><strong>${c.name}</strong></td><td>${c.job_role||'—'}</td><td>${c.package_lpa} LPA</td><td>${c.visit_date||'—'}</td><td><span class="badge ${badge}">${c.status}</span></td></tr>`;
  });
  html += '</tbody></table>';
  document.getElementById('companiesTable').innerHTML = html;
}

async function addStudent() {
  const body = {
    name: document.getElementById('sName').value,
    roll_number: document.getElementById('sRoll').value,
    department: document.getElementById('sDept').value,
    cgpa: parseFloat(document.getElementById('sCgpa').value) || 0,
    email: document.getElementById('sEmail').value,
    phone: document.getElementById('sPhone').value,
    skills: document.getElementById('sSkills').value.split(',').map(s => s.trim()).filter(Boolean),
    tenth_percentage: parseFloat(document.getElementById('sTenth').value) || 0,
    twelfth_percentage: parseFloat(document.getElementById('sTwelfth').value) || 0
  };
  if (!body.name || !body.roll_number) { alert('Name and Roll Number required'); return; }
  await api('/students', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) });
  closeModal('addStudentModal');
  loadStudents();
}

async function addCompany() {
  const body = {
    name: document.getElementById('cName').value,
    industry: document.getElementById('cIndustry').value,
    job_role: document.getElementById('cRole').value,
    package_lpa: parseFloat(document.getElementById('cPackage').value) || 0,
    min_cgpa: parseFloat(document.getElementById('cCgpa').value) || 0,
    visit_date: document.getElementById('cDate').value,
    required_skills: document.getElementById('cSkills').value.split(',').map(s => s.trim()).filter(Boolean),
    job_description: document.getElementById('cDesc').value
  };
  if (!body.name) { alert('Company name required'); return; }
  await api('/companies', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) });
  closeModal('addCompanyModal');
  loadCompanies();
}

// ── Markdown Formatter ──
function formatMarkdown(text) {
  if (!text) return '';
  let html = text
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
  return '<p>' + html + '</p>';
}

// ── Init ──
checkHealth();
loadDashboard();
