# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Setup
```bash
# Windows
setup.bat

# Mac/Linux  
chmod +x setup.sh
./setup.sh
```

### 2. Test Sample Data
```bash
# Process demo calls  
curl -X POST http://localhost:8000/pipeline/process-all/demo

# Process onboarding calls
curl -X POST http://localhost:8000/pipeline/process-all/onboarding

# View results
curl http://localhost:8000/db/accounts
```

### 3. View Generated Files
Check `outputs/accounts/ace_plumbing/` for:
- `v1/account_memo.json` - Initial configuration
- `v2/account_memo.json` - Updated configuration  
- `v2/changelog.json` - What changed

### 4. Access Web Interfaces
- **API Documentation**: http://localhost:8000/docs
- **n8n Workflows**: http://localhost:5678
- **Database Query**: `curl http://localhost:8000/db/accounts`

## 🔧 Process Your Own Data

### Single Account Processing
```bash
curl -X POST http://localhost:8000/pipeline/process/demo \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "my_company",
    "transcript": "Your demo call transcript text..."
  }'
```

### Via n8n Workflows
POST data to:
- Demo: http://localhost:5678/webhook/demo-pipeline
- Onboarding: http://localhost:5678/webhook/onboarding-pipeline  
- Full: http://localhost:5678/webhook/full-pipeline

### Add New Transcripts
1. Save to `dataset/demo/{company}_demo.txt`
2. Save to `dataset/onboarding/{company}_onboarding.txt`  
3. Process via API or workflows

## 🛠️ Troubleshooting

**Services not responding?**
```bash
docker-compose down -v
docker-compose up -d
```

**Check logs:**
```bash
docker-compose logs api
docker-compose logs mongodb
```

**Reset everything:**
```bash
docker-compose down -v
rm -rf outputs/*
docker-compose up -d
```