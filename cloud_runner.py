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
# FREE Job Sources (NO API KEY REQUIRED)
# =============================================================================

# Greenhouse board slugs - https://boards-api.greenhouse.io/v1/boards/{slug}/jobs
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

# Lever board slugs - https://api.lever.co/v0/postings/{slug}
LEVER_COMPANIES = {
    "Netflix": "netflix",
    "Shopify": "shopify",
    "GitLab": "gitlab",
    "Grab": "grab",
    "Notion": "notion",
}

# Ashby board slugs - https://api.ashbyhq.com/posting-api/job-board/{slug}
ASHBY_COMPANIES = {
    "Figma": "figma",
    "Linear": "linear",
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
            "location_preference": ["Hyderabad", "Bangalore", "Chennai", "Pune", "India", "Remote"],
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
    # Source 1: Greenhouse ATS (FREE, no API key)
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
                for item in data.get("jobs", [])[:15]:
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
                time.sleep(0.2)
            except:
                pass
        return jobs

    # =========================================================================
    # Source 2: Lever ATS (FREE, no API key)
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
                for item in data[:15]:
                    categories = item.get("categories", {})
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
                time.sleep(0.2)
            except:
                pass
        return jobs

    # =========================================================================
    # Source 3: Ashby ATS (FREE, no API key)
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
                for item in data.get("jobPostings", [])[:15]:
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
                time.sleep(0.2)
            except:
                pass
        return jobs

    # =========================================================================
    # Source 4: RemoteOK (FREE, no API key)
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
                jobs.append({
                    "title": item.get("position", ""),
                    "company": item.get("company", ""),
                    "location": item.get("location", "Remote"),
                    "salary": f"{item.get('salary_min', '')}-{item.get('salary_max', '')}" if item.get("salary_min") else "Not specified",
                    "url": item.get("url", ""),
                    "source": "RemoteOK",
                    "description": (item.get("description", "") or "")[:500],
                    "posted": item.get("date", ""),
                })
        except Exception as e:
            print(f"  [RemoteOK] Error: {e}")
        return jobs

    # =========================================================================
    # Source 5: Remotive (FREE, no API key)
    # =========================================================================

    def fetch_remotive(self):
        jobs = []
        try:
            r = requests.get("https://remotive.com/api/remote-jobs", headers=self.get_headers(), timeout=15)
            if r.status_code != 200:
                return jobs
            data = r.json()
            for item in data.get("jobs", [])[:50]:
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
    # Source 6: Arbeitnow (FREE, no API key)
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
                    "posted": item.get("created_at", ""),
                })
        except Exception as e:
            print(f"  [Arbeitnow] Error: {e}")
        return jobs

    # =========================================================================
    # Source 7: USAJOBS (FREE, no API key - US government jobs)
    # =========================================================================

    def fetch_usajobs(self):
        jobs = []
        try:
            headers = {
                "User-Agent": "JobMonitor/1.0",
                "Host": "data.usajobs.gov",
            }
            params = {
                "ResultsPerPage": "25",
                "Fields": "min",
            }
            r = requests.get("https://data.usajobs.gov/api/search", headers=headers, params=params, timeout=15)
            if r.status_code != 200:
                return jobs
            data = r.json()
            for item in data.get("SearchResult", {}).get("SearchResultItems", []):
                item = item.get("MatchedObjectDescriptor", {})
                loc = item.get("PositionLocation", [{}])
                loc_str = loc[0].get("CityName", "") + ", " + loc[0].get("CountrySubDivisionCode", "") if loc else "USA"
                jobs.append({
                    "title": item.get("PositionTitle", ""),
                    "company": item.get("OrganizationName", ""),
                    "location": loc_str,
                    "salary": item.get("PositionRemuneration", [{}])[0].get("MinimumRange", "Not specified") if item.get("PositionRemuneration") else "Not specified",
                    "url": item.get("PositionURI", ""),
                    "source": "USAJOBS",
                    "description": (item.get("UserArea", {}).get("Details", {}).get("MajorDuties", [""])[0] if item.get("UserArea", {}).get("Details", {}).get("MajorDuties") else "")[:500],
                    "posted": item.get("PublicationStartDate", ""),
                })
        except Exception as e:
            print(f"  [USAJOBS] Error: {e}")
        return jobs

    # =========================================================================
    # Source 8: IT Jobs (FREE, no API key - Indian job board)
    # =========================================================================

    def fetch_itjobs(self):
        jobs = []
        try:
            r = requests.get("https://www.itjobs.ie/api/jobs", headers=self.get_headers(), timeout=15)
            if r.status_code != 200:
                return jobs
            data = r.json()
            for item in data[:30]:
                jobs.append({
                    "title": item.get("title", ""),
                    "company": item.get("company", ""),
                    "location": item.get("location", "Not specified"),
                    "salary": "Not specified",
                    "url": f"https://www.itjobs.ie/job/{item.get('slug', '')}",
                    "source": "ITJobs",
                    "description": (item.get("description", "") or "")[:500],
                    "posted": item.get("datePosted", ""),
                })
        except Exception as e:
            print(f"  [ITJobs] Error: {e}")
        return jobs

    # =========================================================================
    # Location Matching (India / Hyderabad / South India优先)
    # =========================================================================

    INDIA_KEYWORDS = [
        "india", "hyderabad", "bangalore", "bengaluru", "chennai", "pune",
        "mumbai", "noida", "gurgaon", "delhi", "kolkata", "cochin",
        "coimbatore", "visakhapatnam", "ahmedabad", "jaipur", "lucknow",
        "chandigarh", "thiruvananthapuram", "mysore", "madurai",
        "south india", "remote", "anywhere", "work from home", "wfh",
        "hyd", "blr", "che", "bom", "del",
    ]

    def is_india_location(self, location):
        loc = location.lower()
        return any(kw in loc for kw in self.INDIA_KEYWORDS)

    def location_score(self, location):
        loc = location.lower()
        preferred = self.config.get("preferred_cities", ["hyderabad", "bangalore", "chennai", "pune"])
        for city in preferred:
            if city.lower() in loc:
                return 3  # top priority
        if any(kw in loc for kw in ["india", "hyd", "blr", "che"]):
            return 2
        if any(kw in loc for kw in ["remote", "anywhere", "wfh", "work from home"]):
            return 1
        return 0

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
                <p>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Powered by Job Monitor | 100% Free - No API Keys Required</p>
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

        sources = [
            ("Greenhouse ATS", self.fetch_greenhouse, len(GREENHOUSE_COMPANIES)),
            ("Lever ATS", self.fetch_lever, len(LEVER_COMPANIES)),
            ("Ashby ATS", self.fetch_ashby, len(ASHBY_COMPANIES)),
            ("RemoteOK", self.fetch_remoteok, 0),
            ("Remotive", self.fetch_remotive, 0),
            ("Arbeitnow", self.fetch_arbeitnow, 0),
            ("USAJOBS", self.fetch_usajobs, 0),
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
