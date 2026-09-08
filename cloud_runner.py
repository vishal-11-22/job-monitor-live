import json
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import hashlib
import time
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# =============================================================================
# VERIFIED Working ATS Slugs (tested August 2026)
# =============================================================================

GREENHOUSE = {
    "TCS": "tcs",
    "Figma": "figma",
    "GitLab": "gitlab",
    "Airbnb": "airbnb",
    "Pinterest": "pinterest",
    "DoorDash": "doordash",
    "Stripe": "stripe",
    "Anthropic": "anthropic",
    "Spotify": "spotify",
    "Netflix": "netflix",
    "Uber": "uber",
    "Lyft": "lyft",
    "Snap": "snap-inc",
    "Reddit": "reddit",
    "Discord": "discord",
    "Cloudflare": "cloudflare",
    "CrowdStrike": "crowdstrike",
    "Databricks": "databricks",
    "Datadog": "datadog",
    "Hashicorp": "hashicorp",
    "MongoDB": "mongodb",
    "Twilio": "twilio",
    "Zoom": "zoom",
    "Atlassian": "atlassian",
    "Canva": "canva",
    "Notion": "notion",
    "Vercel": "vercel",
    "Framer": "framer",
    "Linear": "linear",
    "Loom": "loom",
    "Retool": "retool",
    "Webflow": "webflow",
    "Ramp": "ramp",
    "Brex": "brex",
    "Plaid": "plaid",
    "Robinhood": "robinhood",
    "Coinbase": "coinbase",
    "Gusto": "gusto",
    "Rippling": "rippling",
    "Mercury": "mercury",
    "Replit": "replit",
    "OpenAI": "openai",
    "Perplexity": "perplexity",
    "ElevenLabs": "elevenlabs",
}

LEVER = {
    "Netflix": "netflix",
    "Shopify": "shopify",
    "Grab": "grab",
    "Notion": "notion",
    "Figma": "figma",
    "Linear": "linear",
    "N26": "n26",
    "Revolut": "revolut",
    "Klarna": "klarna",
    "UiPath": "uipath",
    "GitLab": "gitlab",
}


class JobMonitor:
    def __init__(self):
        self.config = self.load_config()
        self.seen_file = "seen_jobs.json"
        self.seen_jobs = self.load_json(self.seen_file)
        self.email = os.environ.get('EMAIL_ADDRESS', '')
        self.password = os.environ.get('EMAIL_PASSWORD', '')

    def load_config(self):
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                return json.load(f)
        return {
            "skills": ["Python", "HTML", "CSS", "JavaScript", "MySQL", "Django", "Flask", "Git"],
            "experience_level": "Fresher",
            "preferred_cities": ["Hyderabad", "Bangalore", "Chennai", "Pune"],
        }

    def load_json(self, filename):
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_json(self, filename, data):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def gen_id(self, title, company, url):
        return hashlib.md5(f"{title}_{company}_{url}".encode()).hexdigest()

    def get_headers(self):
        return {'User-Agent': random.choice(USER_AGENTS)}

    # =========================================================================
    # Skill Matching
    # =========================================================================

    def match_skills(self, text):
        text = text.lower()
        matched = []
        aliases = {
            "python": ["python", "django", "flask", "fastapi", "pandas", "numpy", "celery"],
            "html": ["html", "html5"],
            "css": ["css", "css3", "bootstrap", "tailwind", "sass"],
            "javascript": ["javascript", "js", "react", "reactjs", "react.js", "node", "nodejs",
                          "vue", "vuejs", "angular", "typescript", "next.js", "nextjs", "express"],
            "mysql": ["mysql", "sql", "mariadb", "postgresql", "postgres", "sqlite", "mongodb"],
            "django": ["django"],
            "flask": ["flask"],
            "git": ["git", "github", "gitlab", "bitbucket"],
        }
        for skill in self.config.get("skills", []):
            if skill.lower() in text:
                matched.append(skill)
            else:
                for a in aliases.get(skill.lower(), []):
                    if a in text:
                        matched.append(skill)
                        break
        pct = (len(matched) / len(self.config["skills"]) * 100) if self.config.get("skills") else 0
        return round(pct, 1), matched

    # =========================================================================
    # Location Matching (India优先)
    # =========================================================================

    INDIA_KEYWORDS = [
        "india", "hyderabad", "bangalore", "bengaluru", "chennai", "pune",
        "mumbai", "noida", "gurgaon", "delhi", "kolkata", "cochin",
        "coimbatore", "visakhapatnam", "ahmedabad", "jaipur", "lucknow",
        "chandigarh", "thiruvananthapuram", "mysore", "madurai",
        "hyd", "blr", "che", "bom", "del",
    ]

    def location_score(self, location):
        loc = location.lower()
        preferred = self.config.get("preferred_cities", ["hyderabad", "bangalore", "chennai", "pune"])
        for city in preferred:
            if city.lower() in loc:
                return 3
        if any(kw in loc for kw in self.INDIA_KEYWORDS):
            return 2
        if any(kw in loc for kw in ["remote", "anywhere", "wfh", "work from home"]):
            return 1
        return 0

    # =========================================================================
    # Source 1: Greenhouse (FREE, verified slugs)
    # =========================================================================

    def fetch_greenhouse(self):
        jobs = []
        for company_name, slug in GREENHOUSE.items():
            try:
                url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
                r = requests.get(url, headers=self.get_headers(), timeout=10)
                if r.status_code != 200:
                    continue
                data = r.json()
                for item in data.get("jobs", [])[:20]:
                    loc = item.get("location", {})
                    loc_name = loc.get("name", "Not specified") if isinstance(loc, dict) else "Not specified"
                    desc = (item.get("content", "") or "")[:500]
                    jobs.append({
                        "title": item.get("title", ""),
                        "company": company_name,
                        "location": loc_name,
                        "salary": "Not specified",
                        "url": item.get("absolute_url", ""),
                        "source": f"{company_name} (Greenhouse)",
                        "description": desc,
                    })
                time.sleep(0.15)
            except:
                pass
        return jobs

    # =========================================================================
    # Source 2: Lever (FREE, verified slugs)
    # =========================================================================

    def fetch_lever(self):
        jobs = []
        for company_name, slug in LEVER.items():
            try:
                url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
                r = requests.get(url, headers=self.get_headers(), timeout=10)
                if r.status_code != 200:
                    continue
                data = r.json()
                for item in data[:20]:
                    categories = item.get("categories", {})
                    jobs.append({
                        "title": item.get("text", ""),
                        "company": company_name,
                        "location": categories.get("location", "Not specified"),
                        "salary": "Not specified",
                        "url": item.get("hostedUrl", ""),
                        "source": f"{company_name} (Lever)",
                        "description": (item.get("descriptionPlain", "") or "")[:500],
                    })
                time.sleep(0.15)
            except:
                pass
        return jobs

    # =========================================================================
    # Source 3: RemoteOK (FREE)
    # =========================================================================

    def fetch_remoteok(self):
        jobs = []
        try:
            r = requests.get("https://remoteok.com/api", headers=self.get_headers(), timeout=15)
            if r.status_code != 200:
                return jobs
            data = r.json()
            for item in data[1:]:
                if not isinstance(item, dict):
                    continue
                desc = (item.get("description", "") or "")[:500]
                salary_min = item.get("salary_min")
                salary_max = item.get("salary_max")
                salary = f"${salary_min:,}-{salary_max:,}" if salary_min and salary_max else "Not specified"
                jobs.append({
                    "title": item.get("position", ""),
                    "company": item.get("company", ""),
                    "location": item.get("location", "Remote"),
                    "salary": salary,
                    "url": item.get("url", ""),
                    "source": "RemoteOK",
                    "description": desc,
                })
        except Exception as e:
            print(f"  [RemoteOK] Error: {e}")
        return jobs

    # =========================================================================
    # Source 4: Remotive (FREE)
    # =========================================================================

    def fetch_remotive(self):
        jobs = []
        try:
            r = requests.get("https://remotive.com/api/remote-jobs", headers=self.get_headers(), timeout=15)
            if r.status_code != 200:
                return jobs
            data = r.json()
            for item in data.get("jobs", [])[:100]:
                jobs.append({
                    "title": item.get("title", ""),
                    "company": item.get("company_name", ""),
                    "location": item.get("candidate_required_location", "Anywhere"),
                    "salary": item.get("salary", "Not specified"),
                    "url": item.get("url", ""),
                    "source": "Remotive",
                    "description": (item.get("description", "") or "")[:500],
                })
        except Exception as e:
            print(f"  [Remotive] Error: {e}")
        return jobs

    # =========================================================================
    # Source 5: Arbeitnow (FREE)
    # =========================================================================

    def fetch_arbeitnow(self):
        jobs = []
        try:
            r = requests.get("https://www.arbeitnow.com/api/job-board-api", headers=self.get_headers(), timeout=15)
            if r.status_code != 200:
                return jobs
            data = r.json()
            for item in data.get("data", [])[:50]:
                jobs.append({
                    "title": item.get("title", ""),
                    "company": item.get("company_name", ""),
                    "location": item.get("location", "Not specified"),
                    "salary": "Not specified",
                    "url": item.get("url", ""),
                    "source": "Arbeitnow",
                    "description": (item.get("description", "") or "")[:500],
                })
        except Exception as e:
            print(f"  [Arbeitnow] Error: {e}")
        return jobs

    # =========================================================================
    # Source 6: Findwork (FREE)
    # =========================================================================

    def fetch_findwork(self):
        jobs = []
        try:
            r = requests.get("https://findwork.dev/api/jobs/", headers=self.get_headers(), timeout=15)
            if r.status_code != 200:
                return jobs
            data = r.json()
            for item in data.get("results", [])[:50]:
                jobs.append({
                    "title": item.get("role", ""),
                    "company": item.get("company_name", ""),
                    "location": item.get("location", "Not specified") or "Remote",
                    "salary": "Not specified",
                    "url": item.get("url", ""),
                    "source": "Findwork",
                    "description": (item.get("text", "") or "")[:500],
                })
        except Exception as e:
            print(f"  [Findwork] Error: {e}")
        return jobs

    # =========================================================================
    # Source 7: Jobicy (FREE)
    # =========================================================================

    def fetch_jobicy(self):
        jobs = []
        try:
            r = requests.get("https://jobicy.com/api/v2/remote-jobs?count=50&tag=programming", headers=self.get_headers(), timeout=15)
            if r.status_code != 200:
                return jobs
            data = r.json()
            for item in data.get("jobs", []):
                salary_min = item.get("annualSalaryMin")
                salary_max = item.get("annualSalaryMax")
                salary = f"${salary_min:,}-{salary_max:,}" if salary_min and salary_max else "Not specified"
                jobs.append({
                    "title": item.get("jobTitle", ""),
                    "company": item.get("companyName", ""),
                    "location": item.get("jobGeo", "Remote"),
                    "salary": salary,
                    "url": item.get("url", ""),
                    "source": "Jobicy",
                    "description": (item.get("jobDescription", "") or "")[:500],
                })
        except Exception as e:
            print(f"  [Jobicy] Error: {e}")
        return jobs

    # =========================================================================
    # Job Filtering & Dedup
    # =========================================================================

    def filter_jobs(self, jobs):
        new_jobs = []
        for job in jobs:
            search_text = f"{job['title']} {job.get('description', '')} {job['company']}"
            pct, skills = self.match_skills(search_text)
            if pct >= 10:
                jid = self.gen_id(job['title'], job['company'], job['url'])
                if jid not in self.seen_jobs:
                    job['match_pct'] = pct
                    job['matched_skills'] = skills
                    job['loc_score'] = self.location_score(job.get('location', ''))
                    new_jobs.append(job)
                    self.seen_jobs[jid] = {
                        "title": job['title'],
                        "company": job['company'],
                        "source": job['source'],
                        "date": datetime.now().isoformat(),
                    }
        self.save_json(self.seen_file, self.seen_jobs)
        new_jobs.sort(key=lambda x: (x['loc_score'], x['match_pct']), reverse=True)
        return new_jobs

    # =========================================================================
    # Email Notifications
    # =========================================================================

    def send_email(self, jobs):
        if not jobs or not self.email or not self.password:
            return False

        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = self.email
        msg['Subject'] = f"Job Alert: {len(jobs)} New Jobs - Hyderabad/India Priority"

        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 10px; margin-bottom: 20px; }}
                .job-card {{
                    background: white; border-radius: 8px; padding: 18px; margin: 12px 0;
                    border-left: 4px solid #667eea; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .india {{ border-left-color: #ff9933 !important; }}
                .hyderabad {{ border-left-color: #e74c3c !important; }}
                .job-title {{ font-size: 16px; font-weight: bold; color: #333; }}
                .company {{ color: #667eea; font-weight: 600; font-size: 14px; }}
                .detail {{ color: #666; font-size: 13px; margin: 4px 0; }}
                .match-high {{ color: #27ae60; font-weight: bold; }}
                .match-medium {{ color: #f39c12; font-weight: bold; }}
                .match-low {{ color: #e74c3c; font-weight: bold; }}
                .source {{ color: #999; font-size: 11px; font-style: italic; }}
                .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; }}
                .badge-hyderabad {{ background: #e74c3c; color: white; }}
                .badge-india {{ background: #ff9933; color: white; }}
                .badge-remote {{ background: #3498db; color: white; }}
                .apply-btn {{
                    display: inline-block; background: #667eea; color: white;
                    padding: 8px 16px; text-decoration: none; border-radius: 5px;
                    font-size: 13px; margin-top: 8px;
                }}
                .footer {{ color: #999; font-size: 12px; margin-top: 20px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 style="margin:0; font-size:22px;">Job Monitor Alert</h1>
                <p style="margin:5px 0 0 0; font-size:14px;">Found {len(jobs)} new jobs matching your skills</p>
                <p style="margin:2px 0 0 0; font-size:12px;">Skills: {', '.join(self.config.get('skills', []))} | Priority: Hyderabad/South India</p>
            </div>
        """
        for i, j in enumerate(jobs[:25], 1):
            pct = j.get('match_pct', 0)
            loc_score = j.get('loc_score', 0)
            loc = j.get('location', '')

            if pct >= 50:
                match_class = "match-high"
            elif pct >= 25:
                match_class = "match-medium"
            else:
                match_class = "match-low"

            if loc_score == 3:
                card_class = "job-card hyderabad"
                badge = '<span class="badge badge-hyderabad">HYDERABAD</span>'
            elif loc_score == 2:
                card_class = "job-card india"
                badge = '<span class="badge badge-india">INDIA</span>'
            elif loc_score == 1:
                card_class = "job-card"
                badge = '<span class="badge badge-remote">REMOTE</span>'
            else:
                card_class = "job-card"
                badge = ''

            body += f"""
            <div class="{card_class}">
                <div class="job-title">{i}. {j['title']} {badge}</div>
                <div class="company">{j['company']}</div>
                <div class="detail">Location: {loc}</div>
                <div class="detail">Salary: {j.get('salary', 'N/A')}</div>
                <div class="detail"><span class="{match_class}">Match: {pct}%</span> | Skills: {', '.join(j.get('matched_skills', [])[:5])}</div>
                <div class="source">Source: {j['source']}</div>
                <a href="{j['url']}" class="apply-btn" target="_blank">Apply Now</a>
            </div>
            """

        body += f"""
            <div class="footer">
                <p>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Hyderabad/South India jobs shown first</p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as s:
                s.starttls()
                s.login(self.email, self.password)
                s.send_message(msg)
            print("  Email sent successfully")
            return True
        except Exception as e:
            print(f"  Email error: {e}")
            return False

    # =========================================================================
    # Main Run
    # =========================================================================

    def run(self):
        print(f"\n{'='*60}")
        print(f"  Job Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        print(f"  Skills: {', '.join(self.config.get('skills', []))}")
        print(f"  Priority: {', '.join(self.config.get('preferred_cities', []))}")
        print(f"  Seen jobs: {len(self.seen_jobs)}")

        all_jobs = []

        sources = [
            ("Greenhouse ATS", self.fetch_greenhouse, len(GREENHOUSE)),
            ("Lever ATS", self.fetch_lever, len(LEVER)),
            ("RemoteOK", self.fetch_remoteok, 0),
            ("Remotive", self.fetch_remotive, 0),
            ("Arbeitnow", self.fetch_arbeitnow, 0),
            ("Findwork", self.fetch_findwork, 0),
            ("Jobicy", self.fetch_jobicy, 0),
        ]

        for i, (name, fetcher, count) in enumerate(sources, 1):
            label = f"{name}" + (f" ({count} companies)" if count else "")
            print(f"\n[{i}/{len(sources)}] Searching {label}...")
            try:
                found = fetcher()
                print(f"  Found: {len(found)} jobs")
                all_jobs.extend(found)
            except Exception as e:
                print(f"  Error: {e}")

        print(f"\n{'─'*60}")
        print(f"  Total scraped: {len(all_jobs)} jobs")

        new_jobs = self.filter_jobs(all_jobs)
        print(f"  New matches: {len(new_jobs)}")

        india_count = sum(1 for j in new_jobs if j.get('loc_score', 0) >= 2)
        print(f"  India/Hyderabad: {india_count}")

        if new_jobs:
            print(f"\n  Sending email notification...")
            self.send_email(new_jobs)
            print(f"\n  Top matches:")
            for j in sorted(new_jobs, key=lambda x: (x.get('loc_score', 0), x.get('match_pct', 0)), reverse=True)[:10]:
                loc_tag = " [HYD]" if j.get('loc_score') == 3 else " [INDIA]" if j.get('loc_score') == 2 else " [REMOTE]" if j.get('loc_score') == 1 else ""
                print(f"    [{j.get('match_pct', 0):5.1f}%]{loc_tag} {j['title']} @ {j['company']}")
        else:
            print("\n  No new matching jobs found")

        print(f"\n{'='*60}")
        return len(new_jobs)


if __name__ == "__main__":
    monitor = JobMonitor()
    monitor.run()
