# Job Monitor - 24/7 Automated Job Alert System

Automatically monitors job openings from multiple free sources and sends email notifications when jobs match your skills.

## Features

- Runs every 4 hours automatically via GitHub Actions
- Searches LinkedIn, Indeed, Glassdoor (via JSearch API)
- Queries 45+ company ATS systems (Greenhouse, Lever, Ashby)
- Monitors RemoteOK and Remotive for remote jobs
- Smart skill matching with percentage score
- Email alerts with direct apply links
- Deduplication across runs (seen_jobs.json persisted via git)

## Job Sources (All Free)

| Source | Coverage | Free Tier |
|--------|----------|-----------|
| JSearch (Google for Jobs) | LinkedIn, Indeed, Glassdoor, ZipRecruiter | 200 req/month |
| Greenhouse ATS | 45+ companies (Google, Amazon, TCS, Infosys, etc.) | Unlimited |
| Lever ATS | Netflix, Shopify, GitLab, Grab | Unlimited |
| Ashby ATS | Notion, Figma, Linear | Unlimited |
| RemoteOK | Remote jobs worldwide | Unlimited |
| Remotive | Remote tech jobs | Unlimited |

## Setup (3 Steps)

### 1. Fork this repo

### 2. Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | How to get it |
|--------|---------------|
| `EMAIL_ADDRESS` | Your Gmail address |
| `EMAIL_PASSWORD` | Gmail App Password (see below) |
| `RAPIDAPI_KEY` | Free from RapidAPI (see below) |

#### Gmail App Password
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to "App passwords" (search in account settings)
4. Generate a 16-character password

#### RapidAPI Key (Free)
1. Go to https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
2. Sign up (free)
3. Subscribe to the BASIC plan ($0/month, 200 requests)
4. Copy your X-RapidAPI-Key

### 3. Enable GitHub Actions

Go to **Actions** tab → Click "I understand my workflows, go ahead and enable them"

The workflow runs automatically every 4 hours. You can also trigger it manually.

## Customize

### Change Skills
Edit `config.json`:
```json
{
  "skills": ["Python", "React", "Node.js", "Docker"]
}
```

### Change Location
```json
{
  "location_preference": ["India", "Remote", "Hybrid"]
}
```

## Management

- **View runs**: [Actions](https://github.com/vishal-11-22/job-monitor-live/actions)
- **Edit config**: [config.json](https://github.com/vishal-11-22/job-monitor-live/blob/main/config.json)
- **View seen jobs**: [seen_jobs.json](https://github.com/vishal-11-22/job-monitor-live/blob/main/seen_jobs.json)

## How It Works

```
Every 4 hours → GitHub Actions triggers workflow
  → Searches JSearch API (LinkedIn, Indeed, etc.)
  → Queries Greenhouse/Lever/Ashby ATS endpoints
  → Fetches RemoteOK + Remotive feeds
  → Filters by skill match (≥10%)
  → Deduplicates against seen_jobs.json
  → Sends email with new matches
  → Commits seen_jobs.json back to repo
```

## Local Development

```bash
pip install -r requirements.txt
export EMAIL_ADDRESS=your@gmail.com
export EMAIL_PASSWORD=your-app-password
export RAPIDAPI_KEY=your-key
python cloud_runner.py
```
