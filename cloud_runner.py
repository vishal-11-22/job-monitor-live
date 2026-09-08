import json
import os
import smtplib
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import hashlib
from urllib.parse import quote_plus
import random
import time

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

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
            "companies": ["TCS", "Infosys", "Wipro", "HCL", "Cognizant", "Capgemini", "IBM", "Deloitte", "Accenture"],
            "company_career_pages": {
                "Wipro": "https://careers.wipro.com/",
                "HCLTech": "https://www.hcltech.com/careers",
                "Cognizant": "https://www.cognizant.com/careers",
                "Capgemini": "https://www.capgemini.com/careers/",
                "IBM": "https://www.ibm.com/careers",
                "Deloitte": "https://jobs.deloitte.com/",
                "Accenture": "https://www.accenture.com/in-en/careers"
            }
        }

    def load_json(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return {}

    def save_json(self, filename, data):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def gen_id(self, title, company, url):
        return hashlib.md5(f"{title}_{company}_{url}".encode()).hexdigest()

    def get_headers(self):
        return {'User-Agent': random.choice(USER_AGENTS)}

    def match_skills(self, text):
        text = text.lower()
        matched = []
        aliases = {
            "python": ["python", "django", "flask"],
            "html": ["html", "web"],
            "css": ["css", "bootstrap"],
            "javascript": ["javascript", "js", "react", "node"],
            "mysql": ["mysql", "sql"],
            "django": ["django"],
            "flask": ["flask"],
            "git": ["git", "github"]
        }
        for skill in self.config["skills"]:
            if skill.lower() in text:
                matched.append(skill)
            else:
                for a in aliases.get(skill.lower(), []):
                    if a in text:
                        matched.append(skill)
                        break
        pct = (len(matched) / len(self.config["skills"]) * 100) if self.config["skills"] else 0
        return round(pct, 1), matched

    def scrape_linkedin(self):
        jobs = []
        for skill in self.config["skills"][:2]:
            url = f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(skill + ' fresher India')}&location=India"
            try:
                time.sleep(random.uniform(1, 3))
                r = requests.get(url, headers=self.get_headers(), timeout=15)
                soup = BeautifulSoup(r.content, 'html.parser')
                for card in soup.find_all('div', class_='base-card')[:10]:
                    t = card.find('h3', class_='base-search-card__title')
                    c = card.find('h4', class_='base-search-card__subtitle')
                    l = card.find('span', class_='job-search-card__location')
                    a = card.find('a', class_='base-card__full-link')
                    if t and c:
                        jobs.append({
                            "title": t.get_text(strip=True),
                            "company": c.get_text(strip=True),
                            "location": l.get_text(strip=True) if l else "India",
                            "salary": "Check portal",
                            "url": a['href'] if a else "",
                            "source": "LinkedIn"
                        })
            except: pass
        return jobs

    def scrape_career_page(self, name, url):
        jobs = []
        try:
            time.sleep(random.uniform(1, 2))
            r = requests.get(url, headers=self.get_headers(), timeout=15)
            soup = BeautifulSoup(r.content, 'html.parser')
            for link in soup.find_all('a', href=True)[:20]:
                text = link.get_text(strip=True)
                href = link['href']
                if any(k in text.lower() for k in ['job', 'career', 'position', 'apply', 'role']):
                    if not href.startswith('http'):
                        href = f"{url.rstrip('/')}/{href.lstrip('/')}"
                    if len(text) > 5 and len(text) < 150:
                        jobs.append({
                            "title": text,
                            "company": name,
                            "location": "India",
                            "salary": "Not specified",
                            "url": href,
                            "source": f"{name} Careers"
                        })
        except: pass
        return jobs

    def filter_jobs(self, jobs):
        new_jobs = []
        for job in jobs:
            pct, skills = self.match_skills(f"{job['title']} {job['company']}")
            if pct >= 10:
                jid = self.gen_id(job['title'], job['company'], job['url'])
                if jid not in self.seen_jobs:
                    job['match_pct'] = pct
                    job['matched_skills'] = skills
                    new_jobs.append(job)
                    self.seen_jobs[jid] = {"title": job['title'], "company": job['company'], "date": datetime.now().isoformat()}
        self.save_json(self.seen_file, self.seen_jobs)
        return new_jobs

    def send_email(self, jobs):
        if not jobs or not self.email or not self.password:
            return False
        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = self.email
        msg['Subject'] = f"New Jobs Found - {len(jobs)} Matching Your Skills!"
        
        body = f"<html><body><h2>New Job Openings</h2><p>Found {len(jobs)} jobs matching your skills</p>"
        for i, j in enumerate(jobs, 1):
            color = "#27ae60" if j['match_pct'] >= 50 else "#f39c12"
            body += f"""
            <div style='padding:15px;margin:10px 0;border-left:4px solid {color}'>
                <h3>{i}. {j['title']}</h3>
                <p><b>{j['company']}</b></p>
                <p>Location: {j.get('location','N/A')}</p>
                <p>Salary: {j.get('salary','N/A')}</p>
                <p>Match: {j['match_pct']}%</p>
                <p>Skills: {', '.join(j.get('matched_skills',[])[:3])}</p>
                <p>Source: {j['source']}</p>
                <a href='{j['url']}' style='background:#3498db;color:white;padding:8px 15px;text-decoration:none'>Apply</a>
            </div>"""
        body += f"<hr><p style='color:#666;font-size:12px'>Sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></body></html>"
        msg.attach(MIMEText(body, 'html'))
        
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as s:
                s.starttls()
                s.login(self.email, self.password)
                s.send_message(msg)
            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False

    def run(self):
        print(f"Job Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_jobs = []
        
        print("Scraping LinkedIn...")
        all_jobs.extend(self.scrape_linkedin())
        
        print("Scraping career pages...")
        for name, url in self.config.get("company_career_pages", {}).items():
            all_jobs.extend(self.scrape_career_page(name, url))
        
        print(f"Total: {len(all_jobs)} jobs")
        
        new_jobs = self.filter_jobs(all_jobs)
        print(f"New matches: {len(new_jobs)}")
        
        if new_jobs:
            sent = self.send_email(new_jobs)
            print(f"Email: {'Sent' if sent else 'Failed'}")
            for j in new_jobs:
                print(f"  - {j['title']} at {j['company']} ({j['match_pct']}%)")
        
        return len(new_jobs)

if __name__ == "__main__":
    monitor = JobMonitor()
    monitor.run()
