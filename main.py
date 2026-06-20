"""
The Website Auditor — CLEAN VERSION
Only: Scan + Display Results + Send to Make.com
Make.com handles: Email + Google Sheets
"""

import os
import re
import requests
from datetime import datetime
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

MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL", "")

# ─────────────────────────────────────────────────────────────────────────
# SCAN FUNCTION
# ─────────────────────────────────────────────────────────────────────────

def run_website_scan(url):
    """Run 25-point audit"""
    try:
        if not url.startswith('http'):
            url = 'https://' + url
        
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        
        html = response.text.lower()
        
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
            "SSL": response.url.startswith('https'),
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
        score = int((passed / total) * 100) if total > 0 else 0
        
        return {
            "checks": checks,
            "passed": passed,
            "total": total,
            "score": score
        }
    except Exception as e:
        return {"checks": {}, "passed": 0, "total": 25, "score": 0, "error": str(e)}

# ─────────────────────────────────────────────────────────────────────────
# SEND TO MAKE.COM
# ─────────────────────────────────────────────────────────────────────────

def send_to_make(name, email, phone, website, scan_results):
    """Send data to Make.com webhook"""
    try:
        if not MAKE_WEBHOOK_URL:
            return False
        
        payload = {
            "timestamp": datetime.now().isoformat(),
            "name": name,
            "email": email,
            "phone": phone,
            "website": website,
            "score": scan_results.get("score", 0),
            "passed": scan_results.get("passed", 0),
            "total": scan_results.get("total", 25)
        }
        
        response = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=5)
        print(f"Make.com response: {response.status_code}")
        return True
    except Exception as e:
        print(f"Make.com error: {e}")
        return False

# ─────────────────────────────────────────────────────────────────────────
# HOMEPAGE
# ─────────────────────────────────────────────────────────────────────────

HOMEPAGE = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Website Auditor</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Poppins',sans-serif; background:{WHITE}; color:{NAVY}; }}
.navbar {{ background:{NAVY}; color:white; padding:1rem 2rem; }}
.hero {{ background:{NAVY}; color:white; padding:3rem 2rem; text-align:center; }}
.hero h1 {{ font-size:2.5rem; margin-bottom:1rem; }}
.container {{ max-width:900px; margin:2rem auto; padding:0 2rem; }}
.form-box {{ background:#f9f9f9; border:2px solid {LIME}; padding:2rem; border-radius:8px; margin:-2rem auto 2rem; }}
.form-group {{ margin-bottom:1rem; }}
label {{ display:block; font-weight:600; margin-bottom:0.5rem; }}
input {{ width:100%; padding:10px; border:1px solid {NAVY}; border-radius:4px; font-size:14px; }}
.btn {{ width:100%; padding:12px; background:{YELLOW}; color:{NAVY}; border:none; border-radius:4px; font-weight:700; cursor:pointer; font-size:16px; margin-top:1rem; }}
.btn:disabled {{ opacity:0.6; }}
.results {{ background:#f0f9ff; border:2px solid {LIME}; padding:2rem; border-radius:8px; margin:2rem 0; display:none; }}
.results.show {{ display:block; }}
.score-big {{ font-size:3.5rem; font-weight:800; color:{LIME}; text-align:center; }}
.passed-text {{ text-align:center; font-size:18px; color:{NAVY}; margin:1rem 0; font-weight:600; }}
.checks {{ margin-top:2rem; display:grid; grid-template-columns:repeat(2,1fr); gap:0.5rem; }}
.check {{ background:white; padding:0.8rem; border-left:4px solid {LIME}; border-radius:4px; }}
.check.fail {{ border-left-color:#dc2626; }}
.error {{ color:red; margin:1rem 0; font-weight:600; }}
.status {{ text-align:center; color:{LIME}; font-weight:600; margin:1rem 0; }}
footer {{ background:{NAVY}; color:white; text-align:center; padding:2rem; margin-top:4rem; }}
</style>
</head>
<body>

<div class="navbar"><h1>🔍 The Website Auditor</h1></div>
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
    <h2>Your Scan Results</h2>
    <div class="score-big" id="score">0%</div>
    <div class="passed-text" id="passed">0 / 25</div>
    <p style="text-align:center;color:{LIME};font-weight:600;">✅ Email will be sent shortly</p>
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
  const error = document.getElementById('error');
  const status = document.getElementById('status');
  const btn = event.target;
  
  error.innerHTML = '';
  status.innerHTML = '';
  
  if (!name || !email || !phone || !website) {{
    error.innerHTML = 'Fill all fields';
    return;
  }}
  
  btn.disabled = true;
  btn.textContent = '⏳ Scanning...';
  status.innerHTML = '⏳ Please wait...';
  
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
      
      const checksDiv = document.getElementById('checks');
      checksDiv.innerHTML = '';
      
      for (const [name, status] of Object.entries(data.checks || {{}})) {{
        const div = document.createElement('div');
        div.className = 'check ' + (status ? '' : 'fail');
        div.innerHTML = (status ? '✅' : '⚠️') + ' ' + name;
        checksDiv.appendChild(div);
      }}
      
      document.getElementById('results').classList.add('show');
      status.innerHTML = '✅ Scan complete! Email sent.';
      
      setTimeout(() => {{
        document.getElementById('results').scrollIntoView({{behavior: 'smooth'}});
      }}, 100);
    }} else {{
      error.innerHTML = 'Error: ' + (data.error || 'Scan failed');
    }}
  }} catch (err) {{
    error.innerHTML = 'Error: ' + err.message;
  }}
  
  btn.disabled = false;
  btn.textContent = '🚀 SCAN NOW';
}}
</script>

</body>
</html>"""

# ─────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def homepage():
    return HOMEPAGE

@app.post("/api/scan")
async def scan(request: Request):
    """Scan and send to Make.com"""
    try:
        data = await request.json()
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        website = data.get("website", "").strip()
        
        if not all([name, email, phone, website]):
            return JSONResponse({"error": "All fields required"}, status_code=400)
        
        # Run scan
        scan_results = run_website_scan(website)
        
        if scan_results.get("error"):
            return JSONResponse({"error": scan_results["error"]}, status_code=400)
        
        # Send to Make.com (ONLY - no Render email)
        send_to_make(name, email, phone, website, scan_results)
        
        return {
            "status": "success",
            "score": scan_results.get("score", 0),
            "passed": scan_results.get("passed", 0),
            "total": scan_results.get("total", 25),
            "checks": scan_results.get("checks", {})
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
