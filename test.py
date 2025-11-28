# app.py

from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import re

app = Flask(__name__)

# ======= Knowledge / Rule-based response database =======
KB = {
    "adaptive_greeting": {
        "prompt": ["hi", "hello", "hey", "good morning", "good evening", "good afternoon"],
        "reply": lambda: (
            "Good morning!" if 0 <= datetime.now().hour < 12
            else "Good afternoon!" if 12 <= datetime.now().hour < 17
            else "Good evening!"
        )
    },
    "timings": {
        "prompt": ["timing", "hours", "when open", "open", "close", "schedule", "time"],
        "reply": "School hours: Monday–Saturday, 8:00 AM — 2:00 PM. No entry allowed after 8:00AM. 2nd and 4th Saturdays are non instructional. Primary classes end at 1:40PM"
    },
    "fees": {
        "prompt": ["fee", "fees", "tuition", "cost", "price"],
        "reply": "Current fees : Annual tuition ₹55,000, uniform and books not included.TnC apply. Transport extra based on route. Activity fees ₹2,00 per term. for more info: call XXXXXXXXXX"
    },
    "discounts": {
        "prompt": ["discount", "scholarship", "sibling", " concession", "rebate"],
        "reply": "We offer a 10% sibling discount, and a 5% early-payment discount on tuition if paid before April 30 each year.for class 11 students, 10 % discount if student has score 90 percent or above in class 10 CBSE exams and 15% discount on tuition if student scored above 95% in class 10 CBSE exams. for more informatio call XXXXXXXXXX" 
    },
    "policies": {
        "prompt": ["policy", "policies", "rules", "attendance policy", "discipline"],
        "reply": "Key policies: 80% minimum attendance to sit exams,proper uniform required , mobile phones restricted on campus, strict anti-bullying rules."
    },
    "payment": {
        "prompt": ["payment", "pay", "mode", "transaction", "upi", "bank transfer", "online"],
        "reply": "Payments accepted: UPI, netbanking (NEFT/IMPS), credit/debit cards at the office, and cheque. We provide digital invoices on request."
    },
    "history": {
        "prompt": ["history", "founded", "established", "about us", "about"],
        "reply": "Our school was founded in 1972 by Mohini Oberoi mam with a vision of quality afordable education and youth empowerment. Mira Model School has a long history of academic and co-curricular excellence ."
    },
    "attendance": {
        "prompt": ["attendance", "absent", "leave", "attendance rule", "required attendance"],
        "reply": "Students should maintain at least 80% attendance. Submit leave requests via the parent portal or written note to the class teacher."
    },
    "extracurriculars": {
        "prompt": ["extra", "extracurricular", "activities", "clubs", "sports", "music", "dance", "robotics"],
        "reply": "Extra-curriculars: football, basketball, music, dance, art, coding club, robotics and debate. We host a variety of intra school and interschool "
    },
    "syllabus": {
        "prompt": ["syllabus", "curriculum", "cbse", "board", "what we teach"],
        "reply": "We follow the CBSE curriculum with additional life-skills and project-based learning modules."
    },
    "exam_schedule": {
        "prompt": ["exam", "exam schedule", "test", "datesheet", "date sheet", "finals", "midterm"],
        "reply": "Exam schedules are published term-wise in the parent portal and on the notice board. Example: Term 1 exams: Oct 5–10; Term 2 exams: Feb 12–18 (example)."
    },
    "staff": {
        "prompt": ["staff", "teachers", "principal", "head", "teacher info", "faculty"],
        "reply": "We have over 50  teaching staff and 15 support staff. All teachers are certified with average 6+ years teaching experience. Contact details are available on request."
    },
    "amenities": {
        "prompt": ["amenity", "facility", "facilities", "labs", "library", "playground", "bus"],
        "reply": "Facilities: Smart classrooms, Physics,Chemistry,Biology & computer labs, library, playground, art studio, and music room "
    },
    "history_of_payments": {
        "prompt": [ "payment history", "fee history", "invoices", "receipts"],
        "reply": "Parents can view payment history and download receipts from the parent portal under 'Payments'."
    },
    "admission": {
        "prompt": ["admission", "enroll", "registration", "apply", "how to join"],
        "reply": "Admissions: Fill the online application on our admission page, submit required documents and pay the registration fee. Interview and assessment dates are shared later. "
    },
    "transport": {
        "prompt": ["transport", "bus", "bus routes", "pickup", "drop"],
        "reply": "School transport: multiple bus routes with GPS tracking; pick-up times vary by route. Contact transport coordinator for route availability and charges."
    },
    "safety": {
        "prompt": ["safety", "security", "covid", "sanitation", "first aid"],
        "reply": "Safety: CCTV coverage, trained first-aid staff, regular fire drills, and strict visitor check-in procedures."
    },
    "help":{
        "prompt": ["help", "options", "suggestions", "what can i ask", "what to ask"],
        "reply": "You can ask about timings, fees, discounts, admissions, transport, exams, staff, facilities.If you need more information, contact the school office at  011-25508486, 25500489 or email at office@miramodelschooldelhi.edu.in.For admissions related queries email administrator@miramodelschooldelhi.edu.in. For fee related queries email fees@miramodelschooldelhi.edu.in"
    },
    "default": {
        "prompt": [],
        "reply": "Sorry, I didn't get that. You can ask about timings, fees, discounts, admissions, transport, exams, staff, facilities, or say 'help' for suggested prompts."
    }
    
}

# Precompute keyword -> intent map for faster matching
INTENT_KEYWORDS = {}
for intent, data in KB.items():
    for token in data["prompt"]:
        token_norm = token.strip().lower()
        if token_norm:
            INTENT_KEYWORDS[token_norm] = intent

# Helpful quick bank-style suggestions (bank-helper style buttons)
QUICK_SUGGESTIONS = [
    "Timings",
    "Fees",
    "Discounts",
    "Admission process",
    "Exam schedule",
    "Attendance policy",
    "Extracurriculars",
    "Payment modes",
    "Contact staff",
    "Facilities"
]

# ======= Utility: simple keyword-based intent detector =======
def detect_intent(message: str):
    msg = message.lower()
    # direct exact keyword mapping first
    for kw, intent in INTENT_KEYWORDS.items():
        if kw in msg:
            return intent
    # fallback: regex / word token matching (looser)
    words = re.findall(r"\w+", msg)
    for w in words:
        if w in INTENT_KEYWORDS:
            return INTENT_KEYWORDS[w]
    # more advanced: look for stems
    stems = {
        "fee": "fees", "pay": "payment", "exam": "exam_schedule", "test": "exam_schedule",
        "time": "timings", "open": "timings", "close": "timings",
        "bus": "transport", "transport": "transport",
        "admit": "admission", "enroll": "admission"
    }
    for s, intent in stems.items():
        if s in msg:
            return intent
    return "default"

# ======= Routes =======
INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>School Info Chatbot</title>
  <button id="themeToggle" class="theme-btn">🌙</button>

  <meta name="viewport" content="width=device-width,initial-scale=1">

  <style>
    body {
      margin: 0;
      font-family: 'Inter', sans-serif;
      background: linear-gradient(135deg, #0048ff, #00c2ff, #87ffe1);
      background-size: 300% 300%;
      animation: bgShift 10s ease infinite;
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    @keyframes bgShift {
      0% {background-position: 0% 50%;}
      50% {background-position: 100% 50%;}
      100% {background-position: 0% 50%;}
    }

    .app {
      width: 950px;
      max-width: 96vw;
      height: 680px;
      display: grid;
      grid-template-columns: 300px 1fr;
      gap: 20px;
    }

    .left {
      backdrop-filter: blur(18px);
      background: rgba(255,255,255,0.15);
      border-radius: 22px;
      padding: 25px;
      display: flex;
      flex-direction: column;
      box-shadow: 0 8px 40px rgba(0,0,0,0.25);
      border: 1px solid rgba(255,255,255,0.3);
      animation: fadeIn 0.8s ease;
    }

    .logo {
      font-weight: 900;
      font-size: 25px;
      color: #fff;
      margin-bottom: 12px;
      text-shadow: 0 3px 10px rgba(0,0,0,0.5);
    }

    .desc {
      font-size: 14px;
      color: #e6f7ff;
      margin-bottom: 12px;
      line-height: 1.5;
    }

    .quick {
      margin-top: auto;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .chip {
      padding: 10px 14px;
      border-radius: 100px;
      background: rgba(255,255,255,0.3);
      border: 1px solid rgba(255,255,255,0.5);
      backdrop-filter: blur(8px);
      color: #fff;
      cursor: pointer;
      font-size: 13px;
      transition: 0.3s;
    }

    .chip:hover {
      background: rgba(255,255,255,0.7);
      color: #0048ff;
    }

    .right {
      backdrop-filter: blur(15px);
      background: rgba(255,255,255,0.17);
      border-radius: 22px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      box-shadow: 0 8px 40px rgba(0,0,0,0.25);
      border: 1px solid rgba(255,255,255,0.3);
      animation: fadeInUp 0.8s ease;
    }

    @keyframes fadeIn {
      from {opacity: 0; transform: translateY(-20px);}
      to {opacity: 1; transform: translateY(0);}
    }
    @keyframes fadeInUp {
      from {opacity: 0; transform: translateY(30px);}
      to {opacity: 1; transform: translateY(0);}
    }

    .header {
      display: flex;
      align-items: center;
      border-bottom: 1px solid rgba(255,255,255,0.4);
      padding-bottom: 12px;
    }

    .title {
      font-size: 22px;
      color: #fff;
      font-weight: 800;
      text-shadow: 0 2px 10px rgba(0,0,0,0.4);
    }

    .chatbox {
      flex: 1;
      overflow-y: auto;
      padding: 15px;
      display: flex;
      flex-direction: column;
      gap: 15px;
    }

    .msg {
      max-width: 75%;
      padding: 14px 18px;
      border-radius: 20px;
      font-size: 15px;
      line-height: 1.4;
      animation: fadeInUp 0.3s ease;
    }

    .bot {
      align-self: flex-start;
      background: linear-gradient(135deg, #006eff, #00eaff);
      color: white;
      box-shadow: 0 4px 20px rgba(0,0,0,0.25);
      border-bottom-left-radius: 4px;
    }

    .user {
      align-self: flex-end;
      background: rgba(255,255,255,0.9);
      color: #003d6e;
      box-shadow: 0 4px 14px rgba(0,0,0,0.15);
      border-bottom-right-radius: 4px;
    }

    .controls {
      display: flex;
      gap: 10px;
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid rgba(255,255,255,0.3);
    }

    input {
      flex: 1;
      padding: 14px 16px;
      border-radius: 14px;
      border: none;
      outline: none;
      background: rgba(255,255,255,0.85);
      font-size: 14px;
    }

    .send {
      padding: 12px 20px;
      background: linear-gradient(135deg, #00eaff, #006eff);
      color: white;
      border: none;
      border-radius: 14px;
      cursor: pointer;
      font-weight: 600;
      box-shadow: 0 4px 14px rgba(0,0,0,0.25);
      transition: 0.25s;
    }

    .send:hover {
      transform: translateY(-3px);
      box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    }

    .suggest button {
      padding: 8px 12px;
      border-radius: 10px;
      background: rgba(255,255,255,0.25);
      border: none;
      color: #fff;
      cursor: pointer;
      margin: 4px;
      transition: 0.3s;
    }

    .suggest button:hover {
      background: rgba(255,255,255,0.55);
      color: #003d6e;
    }

.theme-btn {
  background: transparent;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--accent-1);
}

.dark-mode {
  --accent-1: #0ea5e9;
  --accent-2: #38bdf8;
  --bg: #0f172a;
  --card: #1e293b;
  background: #0f172a !important;
}
.dark-mode .right,
.dark-mode .left {
  background: #1e293b !important;
  color: #e2e8f0 !important;
}
.dark-mode .msg.bot {
  background: #0ea5e9 !important;
}
.dark-mode .msg.user {
  background: #1e293b !important;
  border: 1px solid #334155;
}

  </style>
</head>

<body>
  <div class="app">

    <div class="left">
      <div class="logo">
        <img src="data:image/jpeg;base64,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" width="55" style="border-radius:10px; vertical-align:middle; margin-right:8px;">
      MAQS: Mira Advanced Query System.
      </div>

      <div class="desc">
        
        Contact info :Phone

Landline: 011-25508486, 25500489

Mobile: 9311125072

office@miramodelschooldelhi.edu.in
administrator@miramodelschooldelhi.edu.in
fees@miramodelschooldelhi.edu.in

​
      </div>

      <div class="quick" id="quick-area"></div>
    </div>

    <div class="right">
      <div class="header">
        <div class="title">Chat Assistant</div>
        <div style="margin-left:auto; color:white;" id="greeting"></div>
      </div>

      <div class="chatbox" id="chatbox"></div>

      <div class="controls">
        <input type="text" id="message" placeholder="Ask something... (e.g. Fees, Timings, Admission)">
        <button class="send" onclick="sendMessage()">Send</button>
      </div>

      <div class="suggest" id="suggestions"></div>
    </div>

  </div>

<script>
const QUICK = {{ quick|tojson }};

function addQuickChips(){
  const q = document.getElementById('quick-area');
  QUICK.forEach(t=>{
    const el=document.createElement('div');
    el.className='chip';
    el.innerText=t;
    el.onclick=()=>setMessageAndSend(t);
    q.appendChild(el);
  });
}
document.getElementById("themeToggle").onclick = () => {
    document.body.classList.toggle("dark-mode");
    let icon = document.getElementById("themeToggle");
    icon.textContent = icon.textContent === "🌙" ? "☀️" : "🌙";
};

function showMessage(text, who='bot'){
  const c=document.getElementById('chatbox');
  const d=document.createElement('div');
  d.className='msg '+(who==='bot'?'bot':'user');
  d.innerText=text;
  c.appendChild(d);
  c.scrollTop=c.scrollHeight;
}

function setMessageAndSend(txt){
  const inp=document.getElementById('message');
  inp.value=txt;
  sendMessage();
}

function clientGreeting(){
  const h=new Date().getHours();
  const g = h<12?'Good morning!':h<17?'Good afternoon!':'Good evening!';
  document.getElementById('greeting').innerText=g;
  showMessage(g + " I'm your school assistant. Ask me anything!");
}

async function sendMessage(){
  const inp=document.getElementById('message');
  const text=inp.value.trim();
  if(!text) return;

  showMessage(text,'user');
  inp.value='';

  const res=await fetch('/chat',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({message:text})
  });

  const data=await res.json();
  data.replies.forEach(r=>showMessage(r,'bot'));
}

addQuickChips();
clientGreeting();
</script>

</body>
</html>
"""

@app.route("/")
def index():
    # Render the HTML template string with quick suggestions
    return render_template_string(INDEX_HTML, quick=QUICK_SUGGESTIONS)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    msg = (data.get("message") or "").strip()
    if not msg:
        return jsonify({"reply": "Please type a question or choose a suggestion."})

    intent = detect_intent(msg)
    kb_entry = KB.get(intent, KB["default"])

    # kb_entry['reply'] may be string or callable (adaptive greeting)
    reply_obj = kb_entry["reply"]
    reply_text = reply_obj() if callable(reply_obj) else reply_obj

    # Create bank-helper style additional replies / clarifications
    additional = []
    if intent == "fees":
        additional = [
            "Would you like a fee breakdown (tuition / activity / transport)?",
            "Need to download invoice or see payment history?"
        ]
    elif intent == "admission":
        additional = [
            "Want the admission form link?",
            "Would you like available seat count by grade?"
        ]
    elif intent == "exam_schedule":
        additional = [
            "I can email the full term calendar or show the dates for a specific class.",
            "Which class/grade's exam schedule would you like?"
        ]
    elif intent == "default":
        additional = [
            "Try: 'Timings', 'Fees', 'Admission', 'Exam schedule', 'Staff info'.",
            "Or type 'help' to see more suggestions."
        ]
    

    # Build response payload with a main reply and quick suggestions
    payload = {
        "intent": intent,
        "replies": [reply_text] + additional[:2],
        "suggest": QUICK_SUGGESTIONS
    }
    return jsonify(payload)

if __name__ == "__main__":
    app.run(debug=True, port=5000)

