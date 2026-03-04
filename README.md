# Clara Answers Automation Pipeline

**Zero-cost automation: Demo Call → Retell Agent → Onboarding Updates**

This pipeline automatically processes call transcripts and generates AI phone agent configurations for Retell.

---

## 📋 What This Does

```
INPUT                           OUTPUT
─────                           ──────
Demo Call Transcript      →     v1 Account Memo + Retell Agent Config
Onboarding Transcript     →     v2 Account Memo + Updated Agent + Changelog
```

### Pipeline A: Demo → Agent v1
- Reads demo call transcript
- Extracts business info (hours, services, contacts, emergency rules)
- Generates Retell agent configuration with system prompt

### Pipeline B: Onboarding → Agent v2
- Reads onboarding call transcript
- Finds updates/changes from the original setup
- Creates v2 with changelog showing what changed

---

## 🚀 Quick Start

### Prerequisites
1. **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop/)
2. **Groq API Key** (FREE) - [Get one here](https://console.groq.com/keys)

### Setup (5 minutes)

```bash
# 1. Navigate to project folder
cd project

# 2. Create your .env file
cp .env.example .env

# 3. Add your Groq API key to .env
# Edit .env and replace gsk_your_key_here with your actual key

# 4. Start Docker Desktop (make sure it's running!)

# 5. Start the containers
docker compose up -d --build

# 6. Wait for services to be ready (~30 seconds)
# Check: docker compose ps
```

### Run via n8n (Recommended)

1. Open n8n: http://localhost:5678
2. Import workflow: `workflows/full_pipeline.json`
3. Click "Execute Workflow"
4. Check outputs in `outputs/accounts/`

### Run via CLI (Alternative)

```bash
# Full pipeline
docker compose exec api python main.py

# Or individual steps
docker compose exec api python main.py demo      # Pipeline A only
docker compose exec api python main.py onboard   # Pipeline B only
```

### API Endpoints (for n8n)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/pipeline/demo` | POST | Run Pipeline A (all demos) |
| `/pipeline/onboarding` | POST | Run Pipeline B (all onboarding) |
| `/pipeline/full` | POST | Run full pipeline |
| `/accounts` | GET | List processed accounts |
| `/accounts/{id}/diff` | GET | View v1 vs v2 changes |

---

## 📁 Project Structure

```
project/
├── dataset/
│   ├── demo/                    # 5 demo call transcripts
│   │   ├── ace_plumbing_demo.txt
│   │   └── ...
│   └── onboarding/              # 5 onboarding transcripts
│       ├── ace_plumbing_onboarding.txt
│       └── ...
│
├── outputs/
│   └── accounts/
│       └── {account_id}/
│           ├── v1/              # Initial configuration
│           │   ├── account_memo.json
│           │   ├── retell_agent_spec.json
│           │   └── RETELL_IMPORT_GUIDE.md
│           └── v2/              # Updated after onboarding
│               ├── account_memo.json
│               ├── changelog.json
│               └── RETELL_IMPORT_GUIDE.md
│
├── src/                         # Core source code
│   ├── __init__.py
│   ├── api.py                   # FastAPI server (n8n calls this)
│   ├── config.py                # Configuration & environment
│   ├── schemas.py               # Pydantic models for LLM output
│   ├── utils.py                 # File operations & helpers
│   ├── extractors/              # LLM extraction modules
│   │   ├── __init__.py
│   │   ├── demo.py              # Pipeline A: Demo call → v1
│   │   └── onboarding.py        # Pipeline B: Onboarding → v2
│   └── generators/              # Agent spec generation
│       ├── __init__.py
│       └── agent_spec.py        # Retell config generator
│
├── workflows/                   # n8n workflow exports
│   ├── full_pipeline.json       # Complete pipeline (recommended)
│   ├── demo_pipeline.json       # Pipeline A only
│   └── onboarding_pipeline.json # Pipeline B only
│
├── main.py                      # CLI pipeline runner
├── Dockerfile                   # Python API container
├── docker-compose.yml           # n8n + API orchestration
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Project configuration
├── docker-compose.yml           # Docker configuration
└── .env.example                 # Environment template
```

---

## 🎯 Running the Pipeline

### Option 1: Run Everything
```bash
docker exec -it project-python-1 python main.py
```

### Option 2: Run Steps Individually
```bash
# Only process demo calls
docker exec -it project-python-1 python main.py demo

# Only process onboarding calls (requires demo to run first)
docker exec -it project-python-1 python main.py onboard

# Only generate agent specs
docker exec -it project-python-1 python main.py agents
```

### Option 3: Use n8n (Visual Automation)
1. Open http://localhost:5678
2. Import `workflows/demo_pipeline.json`
3. Click "Execute Workflow"

---

## 📊 Output Files Explained

### account_memo.json
Structured business data extracted from transcript:
```json
{
  "account_id": "ace_plumbing",
  "company_name": "ACE Plumbing Services",
  "business_hours": {
    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "start": "8:00 AM",
    "end": "6:00 PM",
    "timezone": "EST"
  },
  "services_supported": ["plumbing", "drain cleaning", "water heater repair"],
  "emergency_definition": ["major water leak", "burst pipe", "flooding"],
  "emergency_routing_rules": {
    "primary_contact": "404-555-1234",
    "fallback_contacts": ["404-555-5678"]
  }
}
```

### retell_agent_spec.json
Ready-to-use Retell agent configuration with complete system prompt.

### changelog.json (v2 only)
Shows exactly what changed between v1 and v2:
```json
{
  "transition": "v1 → v2",
  "summary": "Extended hours, added new services, updated emergency contact",
  "changes": [
    {
      "field": "Business Hours",
      "old_value": "8 AM - 6 PM",
      "new_value": "7 AM - 7 PM"
    }
  ]
}
```

---

## 🔧 Configuration

### Environment Variables (.env)
```bash
GROQ_API_KEY=gsk_your_key_here  # Required - free from console.groq.com
RETELL_API_KEY=                  # Optional - for future API integration
```

### Adding Your Own Transcripts
1. Put demo call transcripts in `dataset/demo/` as `.txt` files
2. Put onboarding transcripts in `dataset/onboarding/` as `.txt` files
3. Name files: `{company_name}_demo.txt` and `{company_name}_onboarding.txt`
4. Run the pipeline

---

## 🏆 Zero-Cost Stack

| Component | Tool | Cost |
|-----------|------|------|
| LLM | Groq (Llama 3.1) | FREE |
| Orchestration | n8n (self-hosted) | FREE |
| Storage | Local JSON files | FREE |
| Runtime | Docker containers | FREE |

---

## ⚠️ Troubleshooting

### "Docker daemon not running"
→ Start Docker Desktop and wait for it to fully start

### "GROQ_API_KEY not found"
→ Create `.env` file with your API key (copy from `.env.example`)

### "No v1 memo found"
→ Run demo pipeline first before onboarding: `python main.py demo`

### Containers not starting
```bash
docker compose down
docker compose up -d
docker compose logs
```

---

## 📝 Assignment Compliance

✅ **Zero spend** - All free-tier tools  
✅ **Reproducible** - Docker + clear instructions  
✅ **5 demo + 5 onboarding** - Sample dataset included  
✅ **Account Memo JSON** - Complete structure  
✅ **Retell Agent Spec** - With system prompt  
✅ **Versioning (v1→v2)** - Changelog included  
✅ **n8n Workflow** - Exportable JSON  
✅ **Documentation** - You're reading it!

---

## 🎬 Demo Video Checklist

For your 3-5 minute Loom video, show:
1. [ ] Pipeline running on 1 demo + 1 onboarding pair
2. [ ] Generated outputs (memo, agent spec)
3. [ ] Changelog showing v1 → v2 differences
4. [ ] How to import agent into Retell (manual steps)

---

## 📧 Support

For questions about this implementation, check:
1. The troubleshooting section above
2. Container logs: `docker compose logs`
3. Output files in `outputs/accounts/`
