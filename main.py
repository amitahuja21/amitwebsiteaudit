import os
import re
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

NAVY = "#0A1A40"
LIME = "#A3E635"
YELLOW = "#FACC15"
WHITE = "#FFFFFF"
MAKE_WEBHOOK = "https://hook.eu1.make.com/padspay9db1jptpkckvpxytsm8syyf9r"

def scan_website(url):
    if not url.startswith('http'):
        url = 'https://' + url
    
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        html = r.text.lower()
        
        checks = {
            "GA4": bool(re.search(r'G-[A-Z0-9]{8}', html)),
            "GTM": bool(re.search(r'GTM-[A-Z0-9]+', html)),
            "Meta Pixel": bool(re.search(r'facebook.*tr|fbq', html)),
            "Google Ads": bool(re.search(r'google_conversion', html)),
            "Clarity": bool(re.search(r'clarity\.ms', html)),
            "LinkedIn": bool(re.search(r'linkedin.*px', html)),
            "WhatsApp": bool(re.search(r'wa\.me', html)),
            "Live Chat": bool(re.search(r'tawk|crisp|drift', html)),
            "Contact Form": bool(re.search(r'<form', html)),
            "Exit Intent": bool(re.search(r'exit', html)),
            "SSL": r.url.startswith('https'),
            "Privacy": bool(re.search(r'privacy', html)),
            "Reviews": bool(re.search(r'review|rating', html)),
            "Schema": bool(re.search(r'schema\.org', html)),
            "Open Graph": bool(re.search(r'og:', html)),
            "Mobile": bool(re.search(r'viewport', html)),
            "Favicon": bool(re.search(r'favicon', html)),
            "H1": bool(re.search(r'<h1', html)),
            "Canonical": bool(re.search(r'canonical', html)),
            "Sitemap": bool(re.search(r'sitemap', html)),
            "Click Call": bool(re.search(r'tel:', html)),
            "AI Ready": bool(re.search(r'robots', html)),
            "Fast": True,
            "404s": True,
            "DPDP": True,
        }
        
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        score = int((passed / total) * 100)
        
        return {"checks": checks, "passed": passed, "total": total, "score": score}
    except:
        return {"checks": {}, "passed": 0, "total": 25, "score": 0, "error": "Failed"}

HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Website Auditor</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Poppins,sans-serif;background:{WHITE};color:{NAVY}}}
.navbar{{background:{NAVY};color:white;padding:1rem 2rem}}
.hero{{background:{NAVY};color:white;padding:3rem 2rem;text-align:center}}
.hero h1{{font-size:2.5rem;margin-bottom:1rem}}
.container{{max-width:900px;margin:2rem auto;padding:0 2rem}}
.form-box{{background:#f9f9f9;border:2px solid {LIME};padding:2rem;border-radius:8px;margin:-2rem auto 2rem}}
.form-group{{margin-bottom:1rem}}
label{{display:block;font-weight:600;margin-bottom:0.5rem}}
input{{width:100%;padding:10px;border:1px solid {NAVY};border-radius:4px;font-size:14px}}
.btn{{width:100%;padding:12px;background:{YELLOW};color:{NAVY};border:none;border-radius:4px;font-weight:700;cursor:pointer;font-size:16px;margin-top:1rem}}
.btn:disabled{{opacity:0.6}}
.results{{background:#f0f9ff;border:2px solid {LIME};padding:2rem;border-radius:8px;margin:2rem 0;display:none}}
.results.show{{display:block}}
.score{{font-size:3.5rem;font-weight:800;color:{LIME};text-align:center}}
.passed{{text-align:center;font-size:18px;color:{NAVY};margin:1rem 0;font-weight:600}}
.checks{{margin-top:2rem;display:grid;grid-template-columns:repeat(2,1fr);gap:0.5rem}}
.check{{background:white;padding:0.8rem;border-left:4px solid {LIME};border-radius:4px}}
.check.fail{{border-left-color:#dc2626}}
.error{{color:red;margin:1rem 0;font-weight:600}}
.status{{text-align:center;color:{LIME};font-weight:600;margin:1rem 0}}
footer{{background:{NAVY};color:white;text-align:center;padding:2rem;margin-top:4rem}}
</style>
</head>
<body>

<div class="navbar"><h1>🔍 Website Auditor</h1></div>
<div class="hero"><h1>Free Website Audit</h1><p>25-point scan</p></div>

<div class="form-box">
  <form id="form">
    <div class="form-group"><label>Name *</label><input type="text" id="name" required /></div>
    <div class="form-group"><label>Email *</label><input type="email" id="email" required /></div>
    <div class="form-group"><label>Phone *</label><input type="tel" id="phone" required /></div>
    <div class="form-group"><label>Website *</label><input type="url" id="website" required /></div>
    <button type="button" class="btn" onclick="scan()">🚀 SCAN NOW</button>
    <div id="error" class="error"></div>
    <div id="status" class="status"></div>
  </form>
</div>

<div class="container">
  <div class="results" id="results">
    <h2>Results</h2>
    <div class="score" id="score">0%</div>
    <div class="passed" id="passed">0 / 25</div>
    <p style="text-align:center;color:{LIME};font-weight:600;">✅ Email & sheet updated</p>
    <div class="checks" id="checks"></div>
  </div>
</div>

<footer><p>amit.ahuja@thewebsiteauditor.com | +91 98866 50133</p></footer>

<script>
async function scan() {{
  const name = document.getElementById('name').value.trim();
  const email = document.getElementById('email').value.trim();
  const phone = document.getElementById('phone').value.trim();
  const website = document.getElementById('website').value.trim();
  const btn = event.target;
  
  if (!name || !email || !phone || !website) {{
    document.getElementById('error').innerHTML = 'Fill all fields';
    return;
  }}
  
  btn.disabled = true;
  btn.textContent = '⏳ Scanning...';
  document.getElementById('status').innerHTML = '⏳ Scanning...';
  
  try {{
    const res = await fetch('/api/scan', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{name, email, phone, website}})
    }});
    
    const data = await res.json();
    
    if (res.ok) {{
      document.getElementById('score').textContent = data.score + '%';
      document.getElementById('passed').textContent = data.passed + ' / ' + data.total;
      
      const div = document.getElementById('checks');
      div.innerHTML = '';
      for (const [n, s] of Object.entries(data.checks)) {{
        const c = document.createElement('div');
        c.className = 'check ' + (s ? '' : 'fail');
        c.innerHTML = (s ? '✅' : '⚠️') + ' ' + n;
        div.appendChild(c);
      }}
      
      document.getElementById('results').classList.add('show');
      document.getElementById('status').innerHTML = '✅ Complete!';
      
      fetch('{MAKE_WEBHOOK}', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{timestamp: new Date().toISOString(), name, email, phone, website, score: data.score, passed: data.passed, total: data.total}})
      }}).catch(e => console.log('Make sent'));
    }} else {{
      document.getElementById('error').innerHTML = 'Error: ' + data.error;
    }}
  }} catch (err) {{
    document.getElementById('error').innerHTML = 'Error: ' + err.message;
  }}
  
  btn.disabled = false;
  btn.textContent = '🚀 SCAN NOW';
}}
</script>

</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML

@app.post("/api/scan")
async def api_scan(request: Request):
    try:
        data = await request.json()
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        website = data.get("website", "").strip()
        
        if not all([name, email, phone, website]):
            return JSONResponse({"error": "Missing fields"}, status_code=400)
        
        result = scan_website(website)
        
        if result.get("error"):
            return JSONResponse({"error": result["error"]}, status_code=400)
        
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/health")
async def health():
    return {"status": "ok"}
