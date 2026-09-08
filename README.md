# Job Monitor - 24/7 Automated Job Alert System

Automatically monitors job openings from multiple sources and sends email notifications when jobs match your skills.

## Features

- Runs every hour automatically in the cloud
- Monitors LinkedIn + 40+ company career pages
- Sends email alerts for matching jobs
- Works 24/7 even when PC is off
- Free forever using GitHub Actions

## How to Customize

### Add Companies
Edit `config.json` and add companies to the list:

```json
{
  "companies": ["TCS", "Infosys", "Google", "YourCompany"]
}
Add Skills
Edit config.json and add your skills:
{
  "skills": ["Python", "React", "Node.js", "Docker"]
}
Add Career Pages
Add company career page URLs:
{
  "company_career_pages": {
    "YourCompany": "https://yourcompany.com/careers"
  }
}
Job Sources
- LinkedIn
- Company Career Pages (TCS, Infosys, Wipro, HCL, Cognizant, and more)
Email Notifications
You'll receive emails with:
- Job title and company
- Location and salary
- Skills match percentage
- Direct apply link
Management
- View runs: Actions (https://github.com/vishal-11-22/job-monitor-live/actions)
- Edit config: config.json (https://github.com/vishal-11-22/job-monitor-live/blob/main/config.json)

