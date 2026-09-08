# Job Monitor - 24/7 Automated Job Alert System

Automatically monitors job openings from multiple **100% free** sources and sends email notifications when jobs match your skills.

**No API keys required. No credit card. Completely free forever.**

## Features

- Runs every 4 hours automatically via GitHub Actions
- Searches 45+ company ATS systems directly
- Monitors remote job portals
- Smart skill matching with percentage score
- Email alerts with direct apply links
- Deduplication across runs

## Job Sources (All Free, No API Keys)

| Source | What it covers | Cost |
|--------|---------------|------|
| **Greenhouse ATS** | Google, Amazon, Microsoft, TCS, Infosys, Wipro, +39 more | Free |
| **Lever ATS** | Netflix, Shopify, GitLab, Notion, Grab | Free |
| **Ashby ATS** | Figma, Linear | Free |
| **RemoteOK** | Remote jobs worldwide | Free |
| **Remotive** | Remote tech jobs | Free |
| **Arbeitnow** | International jobs | Free |
| **USAJOBS** | US government jobs | Free |

## Setup (2 Steps)

### 1. Fork this repo

### 2. Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | How to get it |
|--------|---------------|
| `EMAIL_ADDRESS` | Your Gmail address |
| `EMAIL_PASSWORD` | Gmail App Password (see below) |

**That's it! No other API keys needed.**

#### Gmail App Password
1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification**
3. Search **"App passwords"** in account search bar
4. Generate a 16-character password
5. Copy it as the `EMAIL_PASSWORD` secret

### 3. Enable GitHub Actions

Go to **Actions** tab → Click "I understand my workflows, go ahead and enable them"

## Customize

Edit `config.json`:
```json
{
  "skills": ["Python", "React", "Node.js", "Docker"],
  "location_preference": ["India", "Remote", "Hybrid"]
}
```

## Management

- **View runs**: [Actions](https://github.com/vishal-11-22/job-monitor-live/actions)
- **Edit config**: [config.json](https://github.com/vishal-11-22/job-monitor-live/blob/main/config.json)

## How It Works

```
Every 4 hours → GitHub Actions triggers workflow
  → Queries Greenhouse/Lever/Ashby ATS APIs (45+ companies)
  → Fetches RemoteOK + Remotive + Arbeitnow feeds
  → Fetches USAJOBS
  → Filters by skill match (>=10%)
  → Deduplicates against seen_jobs.json
  → Sends email with new matches
  → Commits seen_jobs.json back to repo
```
