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
import re
import xml.etree.ElementTree as ET
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]

COMPANIES = {
    "TCS": {"careers": "https://www.tcs.com/careers", "gh": "tcs"},
    "Infosys": {"careers": "https://www.infosys.com/careers.html"},
    "Wipro": {"careers": "https://www.wipro.com/careers/"},
    "HCLTech": {"careers": "https://www.hcltech.com/careers"},
    "Tech Mahindra": {"careers": "https://www.techmahindra.com/careers"},
    "Cognizant": {"careers": "https://www.cognizant.com/careers", "gh": "cognizant"},
    "Accenture": {"careers": "https://www.accenture.com/in-en/careers"},
    "LTIMindtree": {"careers": "https://www.ltimindtree.com/careers/"},
    "Mphasis": {"careers": "https://www.mphasis.com/careers.html"},
    "Hexaware": {"careers": "https://www.hexaware.com/careers/"},
    "Persistent Systems": {"careers": "https://www.persistent.com/careers/"},
    "Birlasoft": {"careers": "https://www.birlasoft.com/careers"},
    "Zensar Technologies": {"careers": "https://www.zensar.com/careers"},
    "Sonata Software": {"careers": "https://www.sonata-software.com/careers"},
    "Brillio": {"careers": "https://www.brillio.com/careers"},
    "Mastek": {"careers": "https://www.mastek.com/careers"},
    "Cigniti": {"careers": "https://www.cigniti.com/careers"},
    "Qualitest": {"careers": "https://www.qualitestgroup.com/careers/"},
    "Innominds": {"careers": "https://www.innominds.com/careers"},
    "YASH Technologies": {"careers": "https://www.yash.com/careers/"},
    "ValueMomentum": {"careers": "https://www.valuemomentum.com/careers/"},
    "MOURI Tech": {"careers": "https://www.mouritech.com/careers/"},
    "Cloud4C": {"careers": "https://www.cloud4c.com/careers"},
    "Tanla Platforms": {"careers": "https://www.tanla.com/careers"},
    "Kellton": {"careers": "https://www.kellton.com/careers"},
    "4i Apps": {"careers": "https://www.4iapps.com/careers"},
    "Sutherland": {"careers": "https://www.sutherlandglobal.com/careers"},
    "Concentrix": {"careers": "https://www.concentrix.com/careers/"},
    "Marlabs": {"careers": "https://www.marlabs.com/careers/"},
    "Ahex Technologies": {"careers": "https://www.ahextechnologies.com/careers/"},
    "Qcentrio": {"careers": "https://www.qcentrio.com/careers/"},
    "Sasken Technologies": {"careers": "https://www.sasken.com/careers/"},
    "EPAM": {"careers": "https://www.epam.com/careers"},
    "Nagarro": {"careers": "https://www.nagarro.com/careers"},
    "Capgemini": {"careers": "https://www.capgemini.com/careers/"},
    "Coforge": {"careers": "https://www.coforge.com/careers/"},
    "UST": {"careers": "https://www.ust.com/careers"},
    "Virtusa": {"careers": "https://www.virtusa.com/careers/"},
    "Deloitte": {"careers": "https://apply.deloitte.com/careers/Home"},
    "Cyient": {"careers": "https://www.cyient.com/careers"},
    "Thoughtworks": {"careers": "https://www.thoughtworks.com/careers"},
    "Xebia": {"careers": "https://xebia.com/careers"},
    "ValueLabs": {"careers": "https://www.valuelabs.com/careers"},
    "NTT DATA": {"careers": "https://us.nttdata.com/en/careers"},
    "Kyndryl": {"careers": "https://www.kyndryl.com/careers"},
    "Genpact": {"careers": "https://www.genpact.com/careers"},
    "Publicis Sapient": {"careers": "https://www.publicissapient.com/careers"},
    "CGI": {"careers": "https://www.cgi.com/en/careers"},
    "Globant": {"careers": "https://www.globant.com/careers"},
    "IBM": {"careers": "https://www.ibm.com/careers"},
}

GREENHOUSE_SLUGS = {
    "TCS": "tcs", "Cognizant": "cognizant", "Figma": "figma", "GitLab": "gitlab",
    "Airbnb": "airbnb", "Stripe": "stripe", "Anthropic": "anthropic",
    "Spotify": "spotify", "Netflix": "netflix", "Uber": "uber", "Lyft": "lyft",
    "Reddit": "reddit", "Discord": "discord", "Cloudflare": "cloudflare",
    "CrowdStrike": "crowdstrike", "Databricks": "databricks", "Datadog": "datadog",
    "MongoDB": "mongodb", "Twilio": "twilio", "Atlassian": "atlassian",
    "Canva": "canva", "Notion": "notion", "Vercel": "vercel", "Linear": "linear",
    "Webflow": "webflow", "Ramp": "ramp", "Plaid": "plaid", "Robinhood": "robinhood",
    "Coinbase": "coinbase", "Gusto": "gusto", "Rippling": "rippling", "OpenAI": "openai",
}

LEVER_SLUGS = {
    "Netflix": "netflix", "Shopify": "shopify", "Grab": "grab", "Notion": "notion",
    "Figma": "figma", "Linear": "linear", "UiPath": "uipath", "GitLab": "gitlab",
}
INDIA_KEYWORDS = [
    "india", "hyderabad", "bangalore", "bengaluru", "chennai", "pune",
    "mumbai", "noida", "gurgaon", "delhi", "kolkata", "cochin",
    "coimbatore", "visakhapatnam", "ahmedabad", "jaipur", "lucknow",
    "chandigarh", "thiruvananthapuram", "mysore", "madurai", "nagpur",
    "indore", "bhopal", "raipur", "patna", "guwahati", "vadodara",
]

FRESHER_KEYWORDS = [
    "fresher", "trainee", "associate", "junior", "analyst", "intern",
    "graduate", "entry level", "entry-level", "beginner", "campus",
    "0-2 years", "0-1 year", "1-2 years", "0 to 2", "0 to 1",
    "software developer", "data analyst", "business analyst",
    "quality analyst", "test engineer", "devops engineer",
    "cloud engineer", "full stack", "fullstack", "backend developer",
    "frontend developer", "web developer", "python developer",
    "java developer", "react developer", "node developer",
]

SENIOR_KEYWORDS = [
    "senior", "lead", "principal", "staff", "architect", "director",
    "vp ", "vice president", "head of", "chief", "10+ years",
    "12+ years", "15+ years", "20+ years",
]


class JobMonitor:
    def __init__(self):
        self.config = self.load_config()
        self.seen_file = "seen_jobs.json"
        self.seen_jobs = self.load_json(self.seen_file)
        self.email = os.environ.get("EMAIL_ADDRESS", "")
        self.password = os.environ.get("EMAIL_PASSWORD", "")

    def load_config(self):
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                return json.load(f)
        return {
            "skills": ["Python", "HTML", "CSS", "JavaScript", "MySQL", "Django", "Flask", "Git"],
            "experience_level": "Fresher",
            "preferred_cities": ["Hyderabad", "Bangalore", "Chennai", "Pune"],
        }

    def load_json(self, filename):
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_json(self, filename, data):
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

    def gen_id(self, title, company, url):
        return hashlib.md5(f"{title}_{company}_{url}".encode()).hexdigest()

    def get_headers(self):
        return {"User-Agent": random.choice(USER_AGENTS), "Accept": "application/json"}

    def clean_html(self, text):
        if not text:
            return ""
        text = re.sub(r"<[^>]+>", " ", text)
        text = unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:1000]

    def is_india_job(self, location, company=""):
        if not location:
            company_lower = company.lower()
            india_companies = [c.lower() for c in COMPANIES.keys()]
            return any(ic in company_lower for ic in india_companies)
        loc = location.lower()
        if any(kw in loc for kw in INDIA_KEYWORDS):
            return True
        if any(w in loc for w in ["remote", "anywhere", "wfh", "work from home", "work from anywhere"]):
            return True
        return False

    def location_score(self, location):
        if not location:
            return 1
        loc = location.lower()
        preferred = self.config.get("preferred_cities", ["hyderabad", "bangalore", "chennai", "pune"])
        for city in preferred:
            if city.lower() in loc:
                return 4
        if any(kw in loc for kw in ["hyderabad", "hyd", "telangana"]):
            return 3
        south = ["bangalore", "bengaluru", "chennai", "coimbatore", "mysore", "cochin"]
        if any(kw in loc for kw in south):
            return 2
        if any(kw in loc for kw in INDIA_KEYWORDS):
            return 1
        return 0

    def is_fresher_level(self, title, description=""):
        text = f"{title} {description}".lower()
        for kw in SENIOR_KEYWORDS:
            if kw in text:
                return False
        for kw in FRESHER_KEYWORDS:
            if kw in text:
                return True
        exp_match = re.search(r"(\d+)[\s-]*(?:to|-)*\s*(\d*)\s*years?", text)
        if exp_match:
            min_exp = int(exp_match.group(1))
            return min_exp <= 3
        return True

    def match_skills(self, text):
        text = text.lower()
        matched = []
        aliases = {
            "python": ["python", "django", "flask", "fastapi", "pandas", "numpy", "celery", "scipy"],
            "html": ["html", "html5"],
            "css": ["css", "css3", "bootstrap", "tailwind", "sass", "scss"],
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

    def extract_salary(self, text):
        if not text:
            return "Not specified"
        patterns = [
            r"[\u20b9Rs\.]+\s*[\d,]+(?:\s*[-\u2013to]+\s*[\u20b9Rs\.]?\s*[\d,]+)?(?:\s*(?:LPA|Lakh|lakhs|per annum|p\.a\.|annual))?",
            r"\$\d{2,3}k\s*[-\u2013to]+\s*\$?\d{2,3}k",
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return "Not specified"

    def fetch_greenhouse(self):
        jobs = []
        for company_name, slug in GREENHOUSE_SLUGS.items():
            try:
                url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
                r = requests.get(url, headers=self.get_headers(), timeout=12)
                if r.status_code != 200:
                    continue
                data = r.json()
                for item in data.get("jobs", [])[:30]:
                    loc = item.get("location", {})
                    loc_name = loc.get("name", "") if isinstance(loc, dict) else ""
                    if not self.is_india_job(loc_name, company_name):
                        continue
                    desc = self.clean_html(item.get("content", ""))
                    jobs.append({
                        "title": item.get("title", ""),
                        "company": company_name,
                        "location": loc_name or "India",
                        "salary": self.extract_salary(desc),
                        "url": item.get("absolute_url", ""),
                        "source": f"{company_name} (Greenhouse)",
                        "description": desc,
                    })
                time.sleep(0.2)
            except Exception:
                pass
        return jobs

    def fetch_lever(self):
        jobs = []
        for company_name, slug in LEVER_SLUGS.items():
            try:
                url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
                r = requests.get(url, headers=self.get_headers(), timeout=12)
                if r.status_code != 200:
                    continue
                data = r.json()
                for item in data[:30]:
                    categories = item.get("categories", {})
                    loc_name = categories.get("location", "")
                    if not self.is_india_job(loc_name, company_name):
                        continue
                    desc = self.clean_html(item.get("descriptionHtml", "") or item.get("descriptionPlain", ""))
                    jobs.append({
                        "title": item.get("text", ""),
                        "company": company_name,
                        "location": loc_name or "India",
                        "salary": self.extract_salary(desc),
                        "url": item.get("hostedUrl", ""),
                        "source": f"{company_name} (Lever)",
                        "description": desc,
                    })
                time.sleep(0.2)
            except Exception:
                pass
        return jobs

    def fetch_indeed_rss(self):
        jobs = []
        queries = [
            "fresher+python+developer+india", "junior+web+developer+india",
            "trainee+software+engineer+india", "entry+level+data+analyst+india",
            "fresher+full+stack+developer+hyderabad", "fresher+javascript+developer+bangalore",
            "trainee+django+developer+india", "junior+mysql+developer+india",
        ]
        for query in queries:
            try:
                url = f"https://in.indeed.com/rss?q={query}&l=India&sort=date&fromage=7"
                r = requests.get(url, headers=self.get_headers(), timeout=12)
                if r.status_code != 200:
                    continue
                root = ET.fromstring(r.content)
                for item in root.findall(".//item")[:20]:
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    desc_html = item.findtext("description", "")
                    desc = self.clean_html(desc_html)
                    company_match = re.search(r'<span class="company[^"]*">([^<]+)</span>', desc_html or "")
                    company = company_match.group(1).strip() if company_match else "See listing"
                    loc_match = re.search(r'<span class="location[^"]*">([^<]+)</span>', desc_html or "")
                    location = loc_match.group(1).strip() if loc_match else "India"
                    if not self.is_india_job(location, company):
                        continue
                    jobs.append({
                        "title": title, "company": company, "location": location,
                        "salary": "Check listing", "url": link,
                        "source": "Indeed India", "description": desc,
                    })
                time.sleep(0.5)
            except Exception:
                pass
        return jobs

    def fetch_google_jobs_rss(self):
        jobs = []
        queries = [
            "fresher+jobs+in+hyderabad", "junior+developer+jobs+in+bangalore",
            "trainee+software+engineer+jobs+india", "entry+level+python+developer+india",
            "fresher+full+stack+developer+hyderabad", "data+analyst+fresher+jobs+india",
            "web+developer+fresher+jobs+india", "fresher+javascript+developer+india",
        ]
        for query in queries:
            try:
                url = f"https://news.google.com/rss/search?q={query}+when:7d&hl=en-IN&gl=IN&ceid=IN:en"
                r = requests.get(url, headers=self.get_headers(), timeout=12)
                if r.status_code != 200:
                    continue
                root = ET.fromstring(r.content)
                for item in root.findall(".//item")[:15]:
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    desc = item.findtext("description", "")
                    source_tag = item.find("source")
                    source_name = source_tag.text if source_tag is not None else "Google Jobs"
                    company = "See listing"
                    if " - " in title:
                        parts = title.split(" - ")
                        company = parts[-1].strip()
                        title = " - ".join(parts[:-1]).strip()
                    if not self.is_india_job(title + " " + (desc or "") + " " + query, company):
                        continue
                    jobs.append({
                        "title": title, "company": company, "location": "India",
                        "salary": "Check listing", "url": link,
                        "source": f"Google Jobs ({source_name})",
                        "description": self.clean_html(desc or ""),
                    })
                time.sleep(0.5)
            except Exception:
                pass
        return jobs

    def fetch_linkedin_rss(self):
        jobs = []
        queries = [
            "fresher+developer+india", "junior+python+developer+hyderabad",
            "trainee+software+engineer+india", "entry+level+web+developer+bangalore",
            "fresher+data+analyst+india", "junior+javascript+developer+india",
        ]
        for query in queries:
            try:
                url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={query}&location=India&f_TPR=r604800&start=0"
                r = requests.get(url, headers={
                    "User-Agent": random.choice(USER_AGENTS),
                    "Accept": "text/html,application/xhtml+xml",
                }, timeout=12)
                if r.status_code != 200:
                    continue

                class LinkedInParser(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.jobs = []
                        self.current = {}
                        self.in_tag = None
                    def handle_starttag(self, tag, attrs):
                        d = dict(attrs)
                        cls = d.get("class", "")
                        if tag == "a" and "base-card__full-link" in cls:
                            self.current["url"] = d.get("href", "").split("?")[0]
                        if tag == "span" and "screen-reader-text" in cls:
                            self.in_tag = "title"
                        if tag == "a" and "hidden-nested-link" in cls:
                            self.in_tag = "company"
                        if tag == "span" and "job-search-card__location" in cls:
                            self.in_tag = "location"
                    def handle_data(self, data):
                        if self.in_tag:
                            self.current[self.in_tag] = data.strip()
                        self.in_tag = None
                    def handle_endtag(self, tag):
                        if tag == "li" and self.current.get("title"):
                            self.jobs.append(self.current.copy())
                            self.current = {}

                parser = LinkedInParser()
                parser.feed(r.text)
                for j in parser.jobs:
                    loc = j.get("location", "")
                    company = j.get("company", "")
                    if not self.is_india_job(loc, company):
                        continue
                    jobs.append({
                        "title": j.get("title", ""), "company": company,
                        "location": loc, "salary": "Check listing",
                        "url": j.get("url", ""), "source": "LinkedIn",
                        "description": "",
                    })
                time.sleep(0.5)
            except Exception:
                pass
        return jobs

    def fetch_naukri_via_google(self):
        jobs = []
        queries = [
            "fresher+jobs+in+hyderabad+site:naukri.com",
            "python+developer+fresher+india+site:naukri.com",
            "web+developer+fresher+bangalore+site:naukri.com",
            "data+analyst+fresher+india+site:naukri.com",
            "junior+software+engineer+hyderabad+site:naukri.com",
        ]
        for query in queries:
            try:
                url = f"https://www.google.com/search?q={query}&tbm=rss&tbs=qdr:w"
                r = requests.get(url, headers=self.get_headers(), timeout=12)
                if r.status_code != 200:
                    continue
                root = ET.fromstring(r.content)
                for item in root.findall(".//item")[:10]:
                    title = item.findtext("title", "").replace(" - Naukri.com", "").strip()
                    link = item.findtext("link", "")
                    desc_html = item.findtext("description", "")
                    desc = self.clean_html(desc_html)
                    if not self.is_india_job(title + " " + desc, ""):
                        continue
                    jobs.append({
                        "title": title, "company": "See Naukri listing",
                        "location": "India", "salary": "Check listing",
                        "url": link, "source": "Naukri (via Google)",
                        "description": desc,
                    })
                time.sleep(0.5)
            except Exception:
                pass
        return jobs

    def fetch_company_careers(self):
        jobs = []
        career_urls = {
            "TCS": "https://www.tcs.com/content/tcs/global/en/careers/job-search.html",
            "Infosys": "https://www.infosys.com/careers/job-search.html",
            "Wipro": "https://careers.wipro.com/search-jobs",
            "HCLTech": "https://www.hcltech.com/careers/job-search",
            "Cognizant": "https://careers.cognizant.com/global/en/search-results",
            "Accenture": "https://www.accenture.com/in-en/careers/jobsearch?loc=India",
            "Capgemini": "https://www.capgemini.com/careers/job-offers/",
            "IBM": "https://www.ibm.com/careers/search?loc=India",
            "EPAM": "https://www.epam.com/careers/job-listings?location=India",
        }
        for company, url in career_urls.items():
            try:
                r = requests.get(url, headers={
                    "User-Agent": random.choice(USER_AGENTS),
                    "Accept": "text/html,application/xhtml+xml",
                }, timeout=12, allow_redirects=True)
                if r.status_code != 200:
                    continue
                links = re.findall(r'href="([^"]*(?:job|position|opening|career)[^"]*)"', r.text, re.IGNORECASE)
                for link in links[:15]:
                    if not link.startswith("http"):
                        link = urljoin(url, link)
                    title_match = re.search(r'>([^<]{10,80})</a>', r.text[r.text.find(link)-200:r.text.find(link)+200] if link in r.text else "")
                    title = title_match.group(1).strip() if title_match else "Open Position"
                    if not self.is_india_job("India", company):
                        continue
                    jobs.append({
                        "title": title, "company": company, "location": "India",
                        "salary": "Check listing", "url": link,
                        "source": f"{company} (Career Page)", "description": "",
                    })
                time.sleep(0.3)
            except Exception:
                pass
        return jobs

    def fetch_wellfound(self):
        jobs = []
        try:
            url = "https://wellfound.com/role/r/software-engineer/india"
            r = requests.get(url, headers={
                "User-Agent": random.choice(USER_AGENTS), "Accept": "text/html",
            }, timeout=12)
            if r.status_code != 200:
                return jobs
            links = re.findall(r'href="(/startup/\d+/jobs/\d+[^"]*)"', r.text)
            titles = re.findall(r'data-test="StartupResult-name"[^>]*>([^<]+)<', r.text)
            for i, link in enumerate(links[:20]):
                title = titles[i] if i < len(titles) else "Startup Role"
                jobs.append({
                    "title": title, "company": "Startup", "location": "India",
                    "salary": "Check listing", "url": f"https://wellfound.com{link}",
                    "source": "Wellfound", "description": "",
                })
        except Exception:
            pass
        return jobs

    def filter_jobs(self, jobs):
        new_jobs = []
        for job in jobs:
            search_text = f"{job['title']} {job.get('description', '')} {job['company']}"
            pct, skills = self.match_skills(search_text)
            if pct < 10:
                continue
            if not self.is_fresher_level(job["title"], job.get("description", "")):
                continue
            jid = self.gen_id(job["title"], job["company"], job["url"])
            if jid in self.seen_jobs:
                continue
            job["match_pct"] = pct
            job["matched_skills"] = skills
            job["loc_score"] = self.location_score(job.get("location", ""))
            new_jobs.append(job)
            self.seen_jobs[jid] = {
                "title": job["title"], "company": job["company"],
                "source": job["source"], "date": datetime.now().isoformat(),
            }
        self.save_json(self.seen_file, self.seen_jobs)
        new_jobs.sort(key=lambda x: (x["loc_score"], x["match_pct"]), reverse=True)
        return new_jobs

    def send_email(self, jobs):
        if not jobs or not self.email or not self.password:
            return False
        msg = MIMEMultipart()
        msg["From"] = self.email
        msg["To"] = self.email
        hyd = sum(1 for j in jobs if j.get("loc_score", 0) >= 3)
        india = sum(1 for j in jobs if 1 <= j.get("loc_score", 0) <= 2)
        msg["Subject"] = f"Job Alert: {len(jobs)} New Jobs | {hyd} Hyderabad, {india} India"

        html = """<html><head><style>
        body{font-family:Arial,sans-serif;margin:0;padding:20px;background:#f0f2f5}
        .header{background:linear-gradient(135deg,#1a73e8,#0d47a1);color:#fff;padding:25px;border-radius:12px;margin-bottom:20px}
        .stats{display:flex;gap:15px;margin-top:10px}
        .stat{background:rgba(255,255,255,0.2);padding:8px 14px;border-radius:8px;font-size:13px}
        .card{background:#fff;border-radius:10px;padding:18px;margin:10px 0;border-left:4px solid #1a73e8;box-shadow:0 1px 3px rgba(0,0,0,.08)}
        .card-hyd{border-left-color:#e74c3c;background:#fff5f5}
        .card-india{border-left-color:#ff9933;background:#fffaf5}
        .role{font-size:16px;font-weight:700;color:#1a1a1a;margin:0 0 4px 0}
        .company{color:#1a73e8;font-weight:600;font-size:14px}
        .detail{color:#555;font-size:13px;margin:3px 0}
        .skills{color:#0d7c3e;font-weight:600}
        .salary{color:#e65100;font-weight:600}
        .badge{display:inline-block;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:700;margin-left:6px}
        .b-hyd{background:#e74c3c;color:#fff}
        .b-india{background:#ff9933;color:#fff}
        .b-remote{background:#3498db;color:#fff}
        .match{font-weight:700}
        .match-h{color:#0d7c3e}
        .match-m{color:#e65100}
        .match-l{color:#c62828}
        .src{color:#999;font-size:11px;font-style:italic}
        .apply{display:inline-block;background:#1a73e8;color:#fff;padding:8px 18px;text-decoration:none;border-radius:6px;font-size:13px;margin-top:8px}
        .apply:hover{background:#1557b0}
        .footer{color:#999;font-size:12px;margin-top:25px;text-align:center;border-top:1px solid #e0e0e0;padding-top:15px}
        </style></head><body>
        <div class="header">
            <h1 style="margin:0;font-size:22px">Job Monitor Alert</h1>
            <p style="margin:5px 0 0;font-size:14px">Found <b>""" + str(len(jobs)) + """</b> new jobs matching your skills</p>
            <div class="stats">
                <div class="stat">Hyderabad: """ + str(hyd) + """</div>
                <div class="stat">India: """ + str(india) + """</div>
                <div class="stat">Skills: """ + ", ".join(self.config.get("skills", [])) + """</div>
            </div>
        </div>
        """

        for i, j in enumerate(jobs[:30], 1):
            pct = j.get("match_pct", 0)
            loc_s = j.get("loc_score", 0)
            mc = "match-h" if pct >= 50 else "match-m" if pct >= 25 else "match-l"
            if loc_s >= 3:
                cc, badge = "card card-hyd", '<span class="badge b-hyd">HYDERABAD</span>'
            elif loc_s >= 1:
                cc, badge = "card card-india", '<span class="badge b-india">INDIA</span>'
            else:
                cc, badge = "card", ""
            skills_str = ", ".join(j.get("matched_skills", [])[:6])
            html += f"""
            <div class="{cc}">
                <div class="role">{i}. {j['title']} {badge}</div>
                <div class="company">{j['company']}</div>
                <div class="detail">Location: {j.get('location', 'India')}</div>
                <div class="detail salary">Package: {j.get('salary', 'Check listing')}</div>
                <div class="detail skills">Skills Match: {skills_str}</div>
                <div class="detail"><span class="{mc}">Match: {pct}%</span> | Source: {j['source']}</div>
                <a href="{j['url']}" class="apply" target="_blank">Apply Now</a>
            </div>
            """

        html += f"""
        <div class="footer">
            <p>Sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST</p>
            <p>Monitoring 48+ IT companies | India-only | Fresher-level</p>
        </div></body></html>"""

        msg.attach(MIMEText(html, "html"))
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as s:
                s.starttls()
                s.login(self.email, self.password)
                s.send_message(msg)
            print("  Email sent successfully")
            return True
        except Exception as e:
            print(f"  Email error: {e}")
            return False

    def run(self):
        print(f"\n{'='*65}")
        print(f"  Job Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  India-Only | Fresher-Level | 48+ IT Companies")
        print(f"{'='*65}")
        print(f"  Skills: {', '.join(self.config.get('skills', []))}")
        print(f"  Priority: {', '.join(self.config.get('preferred_cities', []))}")
        print(f"  Seen jobs: {len(self.seen_jobs)}")

        all_jobs = []
        sources = [
            ("Greenhouse ATS", self.fetch_greenhouse, len(GREENHOUSE_SLUGS)),
            ("Lever ATS", self.fetch_lever, len(LEVER_SLUGS)),
            ("Indeed India RSS", self.fetch_indeed_rss, 0),
            ("Google Jobs RSS", self.fetch_google_jobs_rss, 0),
            ("LinkedIn Jobs", self.fetch_linkedin_rss, 0),
            ("Naukri (via Google)", self.fetch_naukri_via_google, 0),
            ("Company Career Pages", self.fetch_company_careers, 0),
            ("Wellfound (Startups)", self.fetch_wellfound, 0),
        ]

        for i, (name, fetcher, count) in enumerate(sources, 1):
            label = f"{name}" + (f" ({count} boards)" if count else "")
            print(f"\n[{i}/{len(sources)}] {label}...")
            try:
                found = fetcher()
                print(f"  Found: {len(found)} jobs (India-filtered)")
                all_jobs.extend(found)
            except Exception as e:
                print(f"  Error: {e}")

        print(f"\n{'-'*65}")
        print(f"  Total scraped: {len(all_jobs)} jobs")

        new_jobs = self.filter_jobs(all_jobs)
        print(f"  New matches: {len(new_jobs)}")

        hyd = sum(1 for j in new_jobs if j.get("loc_score", 0) >= 3)
        india = sum(1 for j in new_jobs if 1 <= j.get("loc_score", 0) <= 2)
        print(f"  Hyderabad: {hyd} | India: {india}")

        if new_jobs:
            print(f"\n  Sending email notification...")
            self.send_email(new_jobs)
            print(f"\n  Top 10 matches:")
            for j in new_jobs[:10]:
                loc_tag = " [HYD]" if j.get("loc_score", 0) >= 3 else " [INDIA]" if j.get("loc_score", 0) >= 1 else ""
                print(f"    [{j.get('match_pct', 0):5.1f}%]{loc_tag} {j['title']} @ {j['company']}")
        else:
            print("\n  No new matching jobs found")

        print(f"\n{'='*65}")
        return len(new_jobs)


if __name__ == "__main__":
    monitor = JobMonitor()
    monitor.run()
