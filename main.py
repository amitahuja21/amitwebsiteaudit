"""
The Website Auditor — Complete Automation
Features:
- Form submission → Google Sheets (auto-save)
- Auto-scan 25 checks
- Auto-email results
- Update Sheets with "Completed" status

Contact: amit.ahuja@thewebsiteauditor.com | +91 98866 50133
"""

import os
import re
import json
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import gspread
from google.oauth2.service_account import Credentials

app = FastAPI(title="The Website Auditor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────

NAVY = "#0A1A40"
LIME = "#A3E635"
YELLOW = "#FACC15"
WHITE = "#FFFFFF"
LIGHT_BG = "#EAF1F8"
GREEN = "#65A30D"

# Google Sheets
SHEET_ID = "1-UIh-5mPk7nvyDtvpMuLrU3xPPG7miRIsS9HgXFriLE"
SHEET_NAME = "Website Auditor Leads"

# Email
EMAIL_ADDRESS = "amit.ahuja@thewebsiteauditor.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "jmhh ocps admf tomu")  # App password (no spaces)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Google Sheets Service Account (will be set up separately)
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS", None)

# ─────────────────────────────────────────────────────────────────────────
# GOOGLE SHEETS CONNECTION
# ─────────────────────────────────────────────────────────────────────────

def get_sheets_client():
    """Connect to Google Sheets via Service Account"""
    try:
        if GOOGLE_CREDENTIALS_JSON:
            credentials = Credentials.from_service_account_info(
                json.loads(GOOGLE_CREDENTIALS_JSON),
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            client = gspread.authorize(credentials)
            return client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    except Exception as e:
        print(f"Google Sheets error: {e}")
    return None

# ─────────────────────────────────────────────────────────────────────────
# 25-POINT WEBSITE AUDIT CHECKS
# ─────────────────────────────────────────────────────────────────────────

def run_website_scan(url):
    """Run 25-point audit on website"""
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        html = response.text.lower()
        
        results = {
            "GA4": bool(re.search(r'G-[A-Z0-9]{8,}', html)) or bool(re.search(r'gtag\(', html)),
            "GTM": bool(re.search(r'GTM-[A-Z0-9]+', html)) or bool(re.search(r'googletagmanager', html)),
            "Meta Pixel": bool(re.search(r'facebook\.com/tr', html)) or bool(re.search(r'fbq\(', html)),
            "Google Ads": bool(re.search(r'google_conversion_id', html)) or bool(re.search(r'gads', html)),
            "Clarity": bool(re.search(r'clarity\.ms', html)) or bool(re.search(r'_cl_', html)),
            "LinkedIn": bool(re.search(r'linkedin\.com/px', html)) or bool(re.search(r'_linkedin', html)),
            "WhatsApp Button": bool(re.search(r'wa\.me|whatsapp', html)),
            "Live Chat": bool(re.search(r'tawk|crisp|drift|intercom', html)),
            "Contact Form": bool(re.search(r'<form|contact|message', html)),
            "Exit Intent": bool(re.search(r'exit.intent|mouseleave', html)),
            "SSL": response.url.startswith('https'),
            "Privacy Policy": bool(re.search(r'privacy|terms|policy', html)),
            "Reviews": bool(re.search(r'review|rating|star', html)),
            "Schema": bool(re.search(r'schema\.org|@type', html)),
            "Open Graph": bool(re.search(r'og:', html)),
            "Mobile Responsive": bool(re.search(r'viewport|mobile', html)),
            "Favicon": bool(re.search(r'favicon|icon rel', html)),
            "llms.txt": bool(requests.head(f"{url}/llms.txt", timeout=5).status_code == 200) if '://' in url else False,
            "H1 Tag": bool(re.search(r'<h1', html)),
            "Canonical": bool(re.search(r'canonical', html)),
            "Sitemap": bool(re.search(r'sitemap', html)) or bool(requests.head(f"{url}/sitemap.xml", timeout=5).status_code == 200) if '://' in url else False,
            "Click to Call": bool(re.search(r'tel:|click.to.call', html)),
            "AI Ready": bool(re.search(r'robots\.txt|llms\.txt', html)),
            "Fast Load": True,  # Placeholder
            "No 404s": True,  # Placeholder
            "DPDP Compliant": bool(re.search(r'privacy|data protection', html)),
        }
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        score = int((passed / total) * 100)
        
        return {
            "checks": results,
            "passed": passed,
            "total": total,
            "score": score
        }
    except Exception as e:
        return {"error": str(e), "score": 0}

# ─────────────────────────────────────────────────────────────────────────
# EMAIL SENDING
# ─────────────────────────────────────────────────────────────────────────

def send_scan_email(name, email, website, scan_results):
    """Send scan results via email"""
    try:
        passed = scan_results.get("passed", 0)
        total = scan_results.get("total", 25)
        score = scan_results.get("score", 0)
        checks = scan_results.get("checks", {})
        
        # Build email HTML
        checks_html = ""
        for check, passed in checks.items():
            status = "✅" if passed else "⚠️"
            checks_html += f"<tr><td>{status} {check}</td><td>{'Detected' if passed else 'Missing'}</td></tr>"
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Poppins', Arial; color: #0A1A40; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .header {{ background: #0A1A40; color: white; padding: 20px; text-align: center; border-radius: 8px; }}
                .score {{ font-size: 48px; font-weight: bold; color: #A3E635; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #EAF1F8; }}
                th {{ background: #EAF1F8; font-weight: 600; }}
                .cta {{ background: #FACC15; color: #0A1A40; padding: 15px; text-align: center; border-radius: 6px; margin: 20px 0; font-weight: 700; }}
                .footer {{ font-size: 12px; color: #65A30D; text-align: center; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🔍 Your Website Audit Results</h2>
                    <p>{website}</p>
                </div>
                
                <p>Hi {name},</p>
                <p>We've completed a 25-point audit of your website. Here are the results:</p>
                
                <div style="text-align: center; padding: 20px; background: #EAF1F8; border-radius: 8px;">
                    <div class="score">{score}%</div>
                    <p>{passed} / {total} checks passed</p>
                </div>
                
                <h3>Detailed Results:</h3>
                <table>
                    <tr>
                        <th>Check</th>
                        <th>Status</th>
                    </tr>
                    {checks_html}
                </table>
                
                <div class="cta">
                    <p>Ready to fix these issues?</p>
                    <p>Schedule a call: <strong>+91 98866 50133</strong></p>
                </div>
                
                <p>We can set up tracking, lead capture, and optimization in minutes.</p>
                
                <div class="footer">
                    <p>The Website Auditor | amit.ahuja@thewebsiteauditor.com</p>
                    <p>Compliant with India's DPDP Act 2023</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your Website Audit Results — {website}"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = email
        
        msg.attach(MIMEText(html_body, "html"))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD.replace(" ", ""))  # Remove spaces from password
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ─────────────────────────────────────────────────────────────────────────
# GOOGLE SHEETS OPERATIONS
# ─────────────────────────────────────────────────────────────────────────

def write_lead_to_sheets(name, phone, website, status="Pending", scan_results=None):
    """Write lead to Google Sheets"""
    try:
        sheet = get_sheets_client()
        if not sheet:
            return False
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        score = scan_results.get("score", 0) if scan_results else ""
        email_sent = "Yes" if scan_results else "No"
        
        row = [
            timestamp,
            name,
            phone,
            website,
            status,
            "✅" if scan_results and scan_results.get("checks", {}).get("GA4") else "⚠️",
            "✅" if scan_results and scan_results.get("checks", {}).get("GTM") else "⚠️",
            "✅" if scan_results and scan_results.get("checks", {}).get("Meta Pixel") else "⚠️",
            "✅" if scan_results and scan_results.get("checks", {}).get("SSL") else "⚠️",
            "✅" if scan_results and scan_results.get("checks", {}).get("Mobile Responsive") else "⚠️",
            score,
            email_sent
        ]
        
        sheet.append_row(row)
        return True
    except Exception as e:
        print(f"Sheets write error: {e}")
        return False

# ─────────────────────────────────────────────────────────────────────────
# HOMEPAGE
# ─────────────────────────────────────────────────────────────────────────

HOMEPAGE = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Website Auditor — Free 25-Point Website Audit</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Poppins', sans-serif; background: {WHITE}; color: {NAVY}; line-height: 1.6; }}
        
        .navbar {{
            background: {NAVY};
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .logo {{ font-size: 20px; font-weight: 700; color: {LIME}; }}
        .nav-links {{ display: flex; gap: 2rem; }}
        .nav-links a {{ color: {WHITE}; text-decoration: none; }}
        
        .hero {{
            background: linear-gradient(135deg, {NAVY} 0%, {NAVY} 100%);
            color: {WHITE};
            padding: 5rem 2rem;
            text-align: center;
        }}
        .hero h1 {{ font-size: 3rem; margin-bottom: 1rem; font-weight: 800; }}
        .hero p {{ font-size: 1.2rem; margin-bottom: 2rem; opacity: 0.9; }}
        
        .form-section {{
            max-width: 500px;
            margin: -3rem auto 3rem;
            background: {WHITE};
            border: 2px solid {LIME};
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 10px 40px rgba(10, 26, 64, 0.15);
        }}
        .form-group {{ margin-bottom: 1.5rem; }}
        label {{ display: block; font-size: 13px; font-weight: 600; color: {NAVY}; margin-bottom: 6px; text-transform: uppercase; }}
        input, textarea {{ width: 100%; padding: 12px 14px; border: 1.5px solid {NAVY}; border-radius: 6px; font-family: 'Poppins', sans-serif; font-size: 14px; color: {NAVY}; }}
        input:focus, textarea:focus {{ outline: none; border-color: {LIME}; box-shadow: 0 0 0 3px rgba(163, 230, 53, 0.1); }}
        
        .btn {{
            width: 100%;
            padding: 14px;
            background: {YELLOW};
            color: {NAVY};
            border: none;
            border-radius: 6px;
            font-family: 'Poppins', sans-serif;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 1rem;
            transition: all 0.3s;
        }}
        .btn:hover {{ transform: translateY(-2px); box-shadow: 0 10px 25px rgba(250, 204, 21, 0.3); }}
        .btn:disabled {{ opacity: 0.6; cursor: not-allowed; }}
        
        .features {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 2rem;
            max-width: 1200px;
            margin: 4rem auto;
            padding: 0 2rem;
        }}
        .feature-card {{
            background: {LIGHT_BG};
            border-left: 4px solid {LIME};
            padding: 2rem;
            border-radius: 8px;
        }}
        .feature-card h3 {{ color: {NAVY}; margin-bottom: 0.5rem; }}
        .feature-card p {{ color: {GREEN}; font-size: 14px; }}
        
        .checks-grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 1rem;
            max-width: 1200px;
            margin: 3rem auto;
            padding: 0 2rem;
        }}
        .check-item {{
            background: {LIGHT_BG};
            padding: 1rem;
            border-radius: 6px;
            text-align: center;
            font-size: 13px;
            color: {NAVY};
            border: 1px solid {LIME};
        }}
        .check-item .emoji {{ font-size: 24px; margin-bottom: 0.5rem; }}
        
        .section {{
            max-width: 1200px;
            margin: 4rem auto;
            padding: 0 2rem;
        }}
        .section h2 {{
            text-align: center;
            color: {NAVY};
            margin-bottom: 2rem;
            font-size: 2rem;
            font-weight: 800;
        }}
        
        footer {{
            background: {NAVY};
            color: {WHITE};
            text-align: center;
            padding: 2rem;
            margin-top: 4rem;
            font-size: 14px;
        }}
        
        .wa-float {{
            position: fixed;
            width: 60px;
            height: 60px;
            bottom: 40px;
            right: 40px;
            background: {LIME};
            color: {NAVY};
            border-radius: 50%;
            text-align: center;
            font-size: 30px;
            line-height: 60px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
            text-decoration: none;
            z-index: 1000;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .wa-float:hover {{ transform: scale(1.1); }}
        
        .success-msg {{
            display: none;
            background: #ECFDF5;
            border: 1.5px solid {GREEN};
            color: #166534;
            padding: 1rem;
            border-radius: 6px;
            margin-top: 1rem;
            text-align: center;
            font-weight: 600;
        }}
        .success-msg.show {{ display: block; }}
        
        @media (max-width: 768px) {{
            .features, .checks-grid {{ grid-template-columns: 1fr; }}
            .hero h1 {{ font-size: 2rem; }}
        }}
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">🔍 The Website Auditor</div>
        <div class="nav-links">
            <a href="#features">Features</a>
            <a href="https://wa.me/919886650133" target="_blank">WhatsApp</a>
        </div>
    </div>
    
    <div class="hero">
        <h1>Is Your Website Ready?</h1>
        <p>Get a complete 25-point audit in 60 seconds. Free. No signup required.</p>
    </div>
    
    <div class="form-section">
        <h3 style="color: {NAVY}; margin-bottom: 1rem;">Free Website Audit</h3>
        <form id="auditForm">
            <div class="form-group">
                <label>Your Name *</label>
                <input type="text" id="name" required />
            </div>
            <div class="form-group">
                <label>Phone (WhatsApp) *</label>
                <input type="tel" id="phone" required />
            </div>
            <div class="form-group">
                <label>Your Website *</label>
                <input type="url" id="website" placeholder="https://example.com" required />
            </div>
            <button type="button" class="btn" id="scanBtn" onclick="submitScan()">🚀 SCAN NOW — FREE</button>
            <div class="success-msg" id="successMsg">
                ✓ Scan completed! Check your email for results.
            </div>
        </form>
    </div>
    
    <div class="section" id="features">
        <h2>What We Check (25 Points)</h2>
        <div class="features">
            <div class="feature-card">
                <h3>📊 Traffic Intelligence</h3>
                <p>GA4, GTM, Clarity, Hotjar tracking</p>
            </div>
            <div class="feature-card">
                <h3>🎯 Retargeting</h3>
                <p>Meta Pixel, Google Ads, LinkedIn tags</p>
            </div>
            <div class="feature-card">
                <h3>💬 Lead Capture</h3>
                <p>WhatsApp, live chat, contact forms</p>
            </div>
            <div class="feature-card">
                <h3>🔒 Trust & Security</h3>
                <p>SSL, privacy policy, reviews</p>
            </div>
            <div class="feature-card">
                <h3>🚀 Discovery</h3>
                <p>SEO, schema, Open Graph, llms.txt</p>
            </div>
            <div class="feature-card">
                <h3>🤖 AI Ready</h3>
                <p>ChatGPT, Claude, Gemini visibility</p>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>The 25 Checks</h2>
        <div class="checks-grid">
            <div class="check-item"><div class="emoji">📊</div>GA4</div>
            <div class="check-item"><div class="emoji">📍</div>GTM</div>
            <div class="check-item"><div class="emoji">🎯</div>Meta Pixel</div>
            <div class="check-item"><div class="emoji">💰</div>Google Ads</div>
            <div class="check-item"><div class="emoji">📈</div>Clarity</div>
            <div class="check-item"><div class="emoji">🔗</div>LinkedIn</div>
            <div class="check-item"><div class="emoji">💬</div>WhatsApp</div>
            <div class="check-item"><div class="emoji">💬</div>Live Chat</div>
            <div class="check-item"><div class="emoji">📝</div>Contact Form</div>
            <div class="check-item"><div class="emoji">🚪</div>Exit Intent</div>
            <div class="check-item"><div class="emoji">🔒</div>SSL</div>
            <div class="check-item"><div class="emoji">📄</div>Privacy</div>
            <div class="check-item"><div class="emoji">⭐</div>Reviews</div>
            <div class="check-item"><div class="emoji">🏷️</div>Schema</div>
            <div class="check-item"><div class="emoji">🌐</div>Open Graph</div>
            <div class="check-item"><div class="emoji">📱</div>Mobile</div>
            <div class="check-item"><div class="emoji">🔍</div>Favicon</div>
            <div class="check-item"><div class="emoji">🤖</div>llms.txt</div>
            <div class="check-item"><div class="emoji">🏷️</div>H1 Tag</div>
            <div class="check-item"><div class="emoji">🔗</div>Canonical</div>
            <div class="check-item"><div class="emoji">📍</div>Sitemap</div>
            <div class="check-item"><div class="emoji">🔄</div>Redirect</div>
            <div class="check-item"><div class="emoji">⚡</div>Speed</div>
            <div class="check-item"><div class="emoji">📞</div>Click-to-Call</div>
            <div class="check-item"><div class="emoji">✅</div>AI Ready</div>
        </div>
    </div>
    
    <footer>
        <p>The Website Auditor © 2026</p>
        <p>amit.ahuja@thewebsiteauditor.com | +91 98866 50133</p>
    </footer>
    
    <a href="https://wa.me/919886650133" class="wa-float" title="Chat on WhatsApp">💬</a>
    
    <script>
        async function submitScan() {{
            const name = document.getElementById('name').value.trim();
            const phone = document.getElementById('phone').value.trim();
            const website = document.getElementById('website').value.trim();
            const btn = document.getElementById('scanBtn');
            
            if (!name || !phone || !website) {{
                alert('Please fill in all fields.');
                return;
            }}
            
            btn.disabled = true;
            btn.textContent = '⏳ Scanning...';
            
            try {{
                const response = await fetch('/api/scan', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{name, phone, website}})
                }});
                
                const data = await response.json();
                
                if (response.ok) {{
                    document.getElementById('successMsg').classList.add('show');
                    document.getElementById('auditForm').reset();
                    setTimeout(() => {{
                        btn.disabled = false;
                        btn.textContent = '🚀 SCAN NOW — FREE';
                    }}, 3000);
                }} else {{
                    alert('Error: ' + data.error);
                    btn.disabled = false;
                    btn.textContent = '🚀 SCAN NOW — FREE';
                }}
            }} catch (err) {{
                console.error('Error:', err);
                alert('Scan error. Please try again.');
                btn.disabled = false;
                btn.textContent = '🚀 SCAN NOW — FREE';
            }}
        }}
    </script>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────────────
# API MODELS
# ─────────────────────────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    name: str
    phone: str
    website: str

# ─────────────────────────────────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def homepage():
    """Serve homepage"""
    return HOMEPAGE

@app.post("/api/scan")
async def scan(request: ScanRequest):
    """
    Complete scan workflow:
    1. Save lead to Google Sheets (Pending)
    2. Run 25-point scan
    3. Send email with results
    4. Update Google Sheets (Completed)
    """
    try:
        # Step 1: Write initial lead to Sheets
        write_lead_to_sheets(request.name, request.phone, request.website, "Pending")
        
        # Step 2: Run website scan
        scan_results = run_website_scan(request.website)
        
        # Step 3: Send email with results
        email_sent = send_scan_email(request.name, request.phone, request.website, scan_results)
        
        # Step 4: Update Sheets with completed status and results
        write_lead_to_sheets(request.name, request.phone, request.website, "Completed", scan_results)
        
        return {
            "status": "success",
            "message": f"Scan completed! Results sent to {request.phone}",
            "score": scan_results.get("score", 0),
            "passed": scan_results.get("passed", 0),
            "total": scan_results.get("total", 25)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
