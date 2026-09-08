import json
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import hashlib
import time

# =============================================================================
# Job Sources Configuration
# =============================================================================

# Greenhouse board slugs (free JSON API: https://boards-api.greenhouse.io/v1/boards/{slug}/jobs)
GREENHOUSE_COMPANIES = {
    "Google": "google",
    "Microsoft": "microsoft",
    "Amazon": "amazon",
    "Apple": "apple",
    "Meta": "meta",
    "Accenture": "accenture",
    "IBM": "ibm",
    "Deloitte": "deloitte",
    "Capgemini": "capgemini",
    "Cognizant": "cognizant",
    "Wipro": "wipro",
    "HCLTech": "hcltech",
    "Infosys": "infosys",
    "TCS": "tcs",
    "LTIMindtree": "ltimindtree",
    "Coforge": "coforge",
    "Genpact": "genpact",
    "Persistent Systems": "persistent-systems",
    "Mphasis": "mphasis",
    "UST": "ust",
    "Virtusa": "virtusa",
    "NTT DATA": "nttdata",
    "Hexaware Technologies": "hexaware",
    "DXC Technology": "dxc-technology",
    "EPAM Systems": "epam-systems",
    "Kyndryl": "kyndryl",
    "CGI": "cgi",
    "Birlasoft": "birlasoft",
    "Zensar Technologies": "zensar-technologies",
    "Cyient": "cyient",
    "KPIT Technologies": "kpit-technologies",
    "Sonata Software": "sonata-software",
    "Mastek": "mastek",
    "Sopra Steria": "sopra-steria",
    "eClerx": "eclerx",
    "EXL": "exl",
    "Firstsource": "firstsource",
    "Sutherland": "sutherland",
    "Concentrix": "concentrix",
    "Atos": "atos",
    "3i Infotech": "3i-infotech",
    "Happiest Minds": "happiest-minds",
    "FPT Software": "fpt-software",
    "Tech Mahindra": "tech-mahindra",
}

# Lever board slugs (free JSON API: https://api.lever.co/v0/postings/{slug})
LEVER_COMPANIES = {
    "Netflix": "netflix",
    "Shopify": "shopify",
    "GitLab": "gitlab",
    "Grab": "grab",
}

# Ashby board slugs (free JSON API: https://api.ashbyhq.com/posting-api/job-board/{slug})
ASHBY_COMPANIES = {
    "Notion": "notion",
    "Figma": "figma",
    "Linear": "linear",
}

# Remote job feeds (completely free, no API key needed)
REMOTE_FEEDS = {
    "RemoteOK": "https://remoteok.com/api",
    "Remotive": "https://remotive.com/api/remote-jobs",
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# =============================================================================
# Main Job Monitor
# =============================================================================

class JobMonitor:
    def __init__(self):
        self.config = self.load_config()
        self.seen_file = "seen_jobs.json"
        self.seen_jobs = self.load_json(self.seen_file)
        self.email = os.environ.get('EMAIL_ADDRESS', '')
        self.password = os.environ.get('EMAIL_PASSWORD', '')
        self.rapidapi_key = os.environ.get('RAPIDAPI_KEY', '')
        self.run_count = 0
        self.new_count = 0

    def load_config(self):
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                return json.load(f)
        return {
            "skills": ["Python", "HTML", "CSS", "JavaScript", "MySQL", "Django", "Flask", "Git"],
            "experience_level": "Fresher",
            "location_preference": ["India", "Remote", "Hybrid"],
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
        import random
        return {'User-Agent': random.choice(USER_AGENTS)}

    # =========================================================================
    # Skill Matching
    # =========================================================================

    def match_skills(self, text):
        text = text.lower()
        matched = []
        aliases = {
            "python": ["python", "django", "flask", "fastapi", "pandas", "numpy"],
            "html": ["html", "html5"],
            "css": ["css", "css3", "bootstrap", "tailwind"],
            "javascript": ["javascript", "js", "react", "reactjs", "node", "nodejs", "vue", "angular", "typescript"],
            "mysql": ["mysql", "sql", "mariadb", "postgresql", "postgres"],
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
    # Source 1: JSearch API (Google for Jobs - covers LinkedIn, Indeed, etc.)
    # Free: 200 req/month on RapidAPI
    # =========================================================================

    def fetch_jsearch(self):
        jobs = []
        if not self.rapidapi_key:
            print("  [JSearch] No RAPIDAPI_KEY set, skipping")
            return jobs

        search_queries = [
            f"{' '.join(self.config['skills'][:3])} fresher India",
            f"{' '.join(self.config['skills'][:3])} remote",
            f"{' '.join(self.config['skills'][:2])} junior India",
        ]

        for query in search_queries:
            try:
                url = "https://jsearch.p.rapidapi.com/search"
                params = {
                    "query": query,
                    "page": "1",
                    "num_pages": "1",
                    "date_posted": "week",
                }
                headers = {
                    "X-RapidAPI-Key": self.rapidapi_key,
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
                }
                r = requests.get(url, headers=headers, params=params, timeout=15)
                if r.status_code == 429:
                    print("  [JSearch] Rate limited, stopping")
                    break
                if r.status_code != 200:
                    print(f"  [JSearch] HTTP {r.status_code}")
                    continue

                data = r.json().get("data", [])
                for item in data[:15]:
                    salary = ""
                    if item.get("job_min_salary") and item.get("job_max_salary"):
                        salary = f"{item['job_min_salary']}-{item['job_max_salary']} {item.get('job_salary_currency', 'INR')}"
                    elif item.get("job_min_salary"):
                        salary = f"{item['job_min_salary']}+ {item.get('job_salary_currency', 'INR')}"

                    jobs.append({
                        "title": item.get("job_title", ""),
                        "company": item.get("employer_name", ""),
                        "location": f"{item.get('job_city', '')} {item.get('job_state', '')} {item.get('job_country', '')}".strip() or "Not specified",
                        "salary": salary or "Not specified",
                        "url": item.get("job_apply_link", "") or item.get("job_google_link", ""),
                        "source": "LinkedIn/Indeed (via JSearch)",
                        "description": (item.get("job_description", "") or "")[:500],
                        "posted": item.get("job_posted_at_datetime_utc", ""),
                    })
                time.sleep(1)
            except Exception as e:
                print(f"  [JSearch] Error: {e}")
        return jobs

    # =========================================================================
    # Source 2: Greenhouse ATS (free, no API key)
    # =========================================================================

    def fetch_greenhouse(self):
        jobs = []
        for company_name, slug in GREENHOUSE_COMPANIES.items():
            try:
                url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
                r = requests.get(url, headers=self.get_headers(), timeout=10)
                if r.status_code != 200:
                    continue
                data = r.json()
                for item in data.get("jobs", [])[:20]:
                    loc = item.get("location", {})
                    loc_name = loc.get("name", "Not specified") if isinstance(loc, dict) else "Not specified"
                    jobs.append({
                        "title": item.get("title", ""),
                        "company": company_name,
                        "location": loc_name,
                        "salary": "Not specified",
                        "url": item.get("absolute_url", ""),
                        "source": f"{company_name} (Greenhouse)",
                        "description": (item.get("content", "") or "")[:500],
                        "posted": item.get("updated_at", ""),
                    })
                time.sleep(0.3)
            except:
                pass
        return jobs

    # =========================================================================
    # Source 3: Lever ATS (free, no API key)
    # =========================================================================

    def fetch_lever(self):
        jobs = []
        for company_name, slug in LEVER_COMPANIES.items():
            try:
                url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
                r = requests.get(url, headers=self.get_headers(), timeout=10)
                if r.status_code != 200:
                    continue
                data = r.json()
                for item in data[:20]:
                    categories = item.get("categories", {})
                    teams = item.get("teams", [])
                    team_name = teams[0].get("name", "") if teams else ""
                    jobs.append({
                        "title": item.get("text", ""),
                        "company": company_name,
                        "location": categories.get("location", "Not specified"),
                        "salary": "Not specified",
                        "url": item.get("hostedUrl", ""),
                        "source": f"{company_name} (Lever)",
                        "description": (item.get("descriptionPlain", "") or "")[:500],
                        "posted": item.get("createdAt", ""),
                    })
                time.sleep(0.3)
            except:
                pass
        return jobs

    # =========================================================================
    # Source 4: Ashby ATS (free, no API key)
    # =========================================================================

    def fetch_ashby(self):
        jobs = []
        for company_name, slug in ASHBY_COMPANIES.items():
            try:
                url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
                r = requests.get(url, headers=self.get_headers(), timeout=10)
                if r.status_code != 200:
                    continue
                data = r.json()
                for item in data.get("jobPostings", [])[:20]:
                    location = item.get("locationName", "Not specified")
                    employment = item.get("employmentType", "")
                    jobs.append({
                        "title": item.get("title", ""),
                        "company": company_name,
                        "location": f"{location} ({employment})" if employment else location,
                        "salary": "Not specified",
                        "url": f"https://jobs.ashbyhq.com/{slug}/{item.get('id', '')}",
                        "source": f"{company_name} (Ashby)",
                        "description": (item.get("descriptionPlain", "") or "")[:500],
                        "posted": item.get("postedAt", ""),
                    })
                time.sleep(0.3)
            except:
                pass
        return jobs

    # =========================================================================
    # Source 5: RemoteOK (free JSON feed)
    # =========================================================================

    def fetch_remoteok(self):
        jobs = []
        try:
            r = requests.get("https://remoteok.com/api", headers=self.get_headers(), timeout=15)
            if r.status_code != 200:
                return jobs
            data = r.json()
            for item in data[1:]:  # first item is metadata
                if not isinstance(item, dict):
                    continue
                tags = item.get("tags", [])
                title = item.get("position", "")
                company = item.get("company", "")
                desc = item.get("description", "") or ""
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": item.get("location", "Remote"),
                    "salary": f"{item.get('salary_min', '')}-{item.get('salary_max', '')}" if item.get("salary_min") else "Not specified",
                    "url": item.get("url", ""),
                    "source": "RemoteOK",
                    "description": desc[:500],
                    "posted": item.get("date", ""),
                })
        except Exception as e:
            print(f"  [RemoteOK] Error: {e}")
        return jobs

    # =========================================================================
    # Source 6: Remotive (free JSON feed)
    # =========================================================================

    def fetch_remotive(self):
        jobs = []
        try:
            r = requests.get("https://remotive.com/api/remote-jobs", headers=self.get_headers(), timeout=15)
            if r.status_code != 200:
                return jobs
            data = r.json()
            for item in data.get("jobs", [])[:50]:
                tags = item.get("tags", [])
                jobs.append({
                    "title": item.get("title", ""),
                    "company": item.get("company_name", ""),
                    "location": item.get("candidate_required_location", "Anywhere"),
                    "salary": item.get("salary", "Not specified"),
                    "url": item.get("url", ""),
                    "source": "Remotive",
                    "description": (item.get("description", "") or "")[:500],
                    "posted": item.get("publication_date", ""),
                })
        except Exception as e:
            print(f"  [Remotive] Error: {e}")
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
                    new_jobs.append(job)
                    self.seen_jobs[jid] = {
                        "title": job['title'],
                        "company": job['company'],
                        "source": job['source'],
                        "date": datetime.now().isoformat(),
                    }
        self.save_json(self.seen_file, self.seen_jobs)
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
        msg['Subject'] = f"Job Alert: {len(jobs)} New Matching Jobs Found!"

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
                .job-title {{ font-size: 16px; font-weight: bold; color: #333; margin-bottom: 5px; }}
                .company {{ color: #667eea; font-weight: 600; font-size: 14px; }}
                .detail {{ color: #666; font-size: 13px; margin: 4px 0; }}
                .match-high {{ color: #27ae60; font-weight: bold; }}
                .match-medium {{ color: #f39c12; font-weight: bold; }}
                .match-low {{ color: #e74c3c; font-weight: bold; }}
                .source {{ color: #999; font-size: 11px; font-style: italic; }}
                .apply-btn {{
                    display: inline-block; background: #667eea; color: white;
                    padding: 8px 16px; text-decoration: none; border-radius: 5px;
                    font-size: 13px; margin-top: 8px;
                }}
                .apply-btn:hover {{ background: #5a6fd6; }}
                .footer {{ color: #999; font-size: 12px; margin-top: 20px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 style="margin:0; font-size:22px;">Job Monitor Alert</h1>
                <p style="margin:5px 0 0 0; font-size:14px;">Found {len(jobs)} new jobs matching your skills</p>
                <p style="margin:2px 0 0 0; font-size:12px;">Skills: {', '.join(self.config.get('skills', []))}</p>
            </div>
        """
        for i, j in enumerate(jobs[:20], 1):
            pct = j.get('match_pct', 0)
            if pct >= 50:
                match_class = "match-high"
                badge = "HIGH MATCH"
            elif pct >= 25:
                match_class = "match-medium"
                badge = "GOOD MATCH"
            else:
                match_class = "match-low"
                badge = "POSSIBLE MATCH"

            body += f"""
            <div class="job-card">
                <div class="job-title">{i}. {j['title']}</div>
                <div class="company">{j['company']}</div>
                <div class="detail">Location: {j.get('location', 'N/A')}</div>
                <div class="detail">Salary: {j.get('salary', 'N/A')}</div>
                <div class="detail"><span class="{match_class}">Match: {pct}% - {badge}</span></div>
                <div class="detail">Skills: {', '.join(j.get('matched_skills', [])[:5])}</div>
                <div class="source">Source: {j['source']}</div>
                <a href="{j['url']}" class="apply-btn" target="_blank">Apply Now</a>
            </div>
            """

        body += f"""
            <div class="footer">
                <p>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                <p>Powered by Job Monitor | Sources: JSearch, Greenhouse, Lever, Ashby, RemoteOK, Remotive</p>
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
        print(f"  Seen jobs: {len(self.seen_jobs)}")

        all_jobs = []

        # Source 1: JSearch (Google for Jobs)
        print("\n[1/6] Searching JSearch (LinkedIn, Indeed, Glassdoor)...")
        jsearch_jobs = self.fetch_jsearch()
        print(f"  Found: {len(jsearch_jobs)} jobs")
        all_jobs.extend(jsearch_jobs)

        # Source 2: Greenhouse ATS
        print("\n[2/6] Searching Greenhouse ATS...")
        gh_jobs = self.fetch_greenhouse()
        print(f"  Found: {len(gh_jobs)} jobs from {len(GREENHOUSE_COMPANIES)} companies")
        all_jobs.extend(gh_jobs)

        # Source 3: Lever ATS
        print("\n[3/6] Searching Lever ATS...")
        lever_jobs = self.fetch_lever()
        print(f"  Found: {len(lever_jobs)} jobs from {len(LEVER_COMPANIES)} companies")
        all_jobs.extend(lever_jobs)

        # Source 4: Ashby ATS
        print("\n[4/6] Searching Ashby ATS...")
        ashby_jobs = self.fetch_ashby()
        print(f"  Found: {len(ashby_jobs)} jobs from {len(ASHBY_COMPANIES)} companies")
        all_jobs.extend(ashby_jobs)

        # Source 5: RemoteOK
        print("\n[5/6] Searching RemoteOK...")
        remoteok_jobs = self.fetch_remoteok()
        print(f"  Found: {len(remoteok_jobs)} remote jobs")
        all_jobs.extend(remoteok_jobs)

        # Source 6: Remotive
        print("\n[6/6] Searching Remotive...")
        remotive_jobs = self.fetch_remotive()
        print(f"  Found: {len(remotive_jobs)} remote jobs")
        all_jobs.extend(remotive_jobs)

        print(f"\n{'─'*60}")
        print(f"  Total scraped: {len(all_jobs)} jobs")

        # Filter & dedup
        new_jobs = self.filter_jobs(all_jobs)
        print(f"  New matches: {len(new_jobs)}")

        # Send email
        if new_jobs:
            print(f"\n  Sending email notification...")
            self.send_email(new_jobs)
            print(f"\n  Top matches:")
            for j in sorted(new_jobs, key=lambda x: x.get('match_pct', 0), reverse=True)[:10]:
                print(f"    [{j.get('match_pct', 0):5.1f}%] {j['title']} @ {j['company']} ({j['source']})")
        else:
            print("\n  No new matching jobs found")

        print(f"\n{'='*60}")
        return len(new_jobs)


if __name__ == "__main__":
    monitor = JobMonitor()
    monitor.run()
