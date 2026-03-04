# Agent Pipeline - AI Phone Agent Configuration System

🤖 **Automated business rule extraction and AI phone agent configuration from call transcripts**

## Overview

Agent Pipeline transforms unstructured sales and onboarding call transcripts into structured AI phone agent configurations. The system processes demo calls to create initial agent setups (v1) and onboarding calls to refine them (v2), automating 90% of phone service configuration.

## 🏗️ Architecture

```
Demo Call → AI Extraction → v1 Agent Config
                ↓
Onboarding Call → AI Updates → v2 Agent Config → MongoDB Storage
```

**Components:**
- **FastAPI**: REST API server for processing
- **MongoDB**: Configuration data storage  
- **n8n**: Workflow orchestration
- **Groq LLM**: AI extraction via LangChain
- **Docker**: Containerized deployment

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Groq API key ([get one here](https://console.groq.com/))

### 1. Clone & Configure
```bash
git clone <repository>
cd project

# Set your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env
```

### 2. Start Services
```bash
docker-compose up -d
```

This starts:
- **API Server**: http://localhost:8000
- **MongoDB**: localhost:27017 (admin/password)
- **n8n Workflows**: http://localhost:5678

### 3. Verify Setup
```bash
# Check API health
curl http://localhost:8000/health

# Check database
curl http://localhost:8000/db/health

# List any existing accounts
curl http://localhost:8000/db/accounts
```

## 📋 Usage

### Processing Demo Calls (Create v1)

**Via API:**
```bash
curl -X POST http://localhost:8000/pipeline/process/demo \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "ace_plumbing",
    "transcript": "Demo call transcript text here..."
  }'
```

**Via n8n Workflow:**  
POST to `http://localhost:5678/webhook/demo-pipeline`

### Processing Onboarding Calls (Update to v2)

**Via API:**
```bash
curl -X POST http://localhost:8000/pipeline/process/onboarding \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "ace_plumbing", 
    "transcript": "Onboarding call transcript...",
    "v1_memo": null
  }'
```

**Via n8n Workflow:**  
POST to `http://localhost:5678/webhook/onboarding-pipeline`

### Full Pipeline (Demo → Onboarding)

POST to `http://localhost:5678/webhook/full-pipeline` with:
```json
{
  "account_id": "company_name",
  "demo_transcript": "Demo call text...",
  "onboarding_transcript": "Onboarding call text..." 
}
```

## 🔌 API Endpoints

### Pipeline Processing
- `POST /pipeline/process/demo` - Process demo calls → v1
- `POST /pipeline/process/onboarding` - Process onboarding → v2  
- `GET /pipeline/health` - Check pipeline status

### Database Operations
- `GET /db/accounts` - List all accounts
- `GET /db/accounts/{id}?version=v1|v2` - Get account data
- `GET /db/accounts/{id}/memo?version=v1|v2` - Get account memo only
- `POST /db/save` - Save account data (used by workflows)
- `DELETE /db/accounts/{id}?version=v1|v2` - Delete account
- `GET /db/health` - Check MongoDB connection

### System Health
- `GET /health` - Overall system health

## 📁 Data Structure

### Generated Files (per account)
```
outputs/accounts/{account_id}/
├── v1/                          # Demo processing results
│   ├── account_memo.json        # Business configuration
│   ├── retell_agent_spec.json   # AI agent specification  
│   └── raw_extraction.json      # Raw AI extraction
└── v2/                          # Onboarding processing results
    ├── account_memo.json        # Updated configuration
    ├── retell_agent_spec.json   # Updated agent spec
    ├── changelog.json           # v1→v2 changes
    └── raw_updates.json         # Raw update extraction
```

### Sample Account Memo Structure
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
  "services_supported": ["residential plumbing", "drain cleaning"],
  "emergency_definition": ["major water leaks", "burst pipes"],
  "emergency_routing_rules": {
    "primary_contact": "404-555-1234",
    "fallback_contacts": ["404-555-5678"],
    "timeout_seconds": 30
  },
  "integration_constraints": ["Do not offer: pool plumbing"],
  "special_instructions": ["ask for caller's address"],
  "service_area": "greater Atlanta metro area"
}
```

## 📊 Database Storage

All data is stored in MongoDB with identical structure to output files:

**Database Collections:**
- `accounts` - Account configurations with versions

**Query Examples:**
```bash
# List all accounts
curl http://localhost:8000/db/accounts

# Get v1 configuration  
curl "http://localhost:8000/db/accounts/ace_plumbing?version=v1"

# Get v2 configuration
curl "http://localhost:8000/db/accounts/ace_plumbing?version=v2"

# Get just the business rules memo
curl "http://localhost:8000/db/accounts/ace_plumbing/memo?version=v2"
```

## 🛠️ Development

### Project Structure
```
src/
├── api/routers/          # FastAPI endpoints
│   ├── accounts.py       # Account management  
│   ├── pipeline.py       # Processing endpoints
│   ├── dataset.py        # Dataset operations
│   └── db.py            # Database operations
├── extractors/          # AI processing modules
│   ├── demo.py          # Demo call processing
│   └── onboarding.py    # Onboarding call processing
├── generators/          # Output generation
│   └── agent_spec.py    # Retell agent spec generation
├── db/                  # Database layer
│   └── __init__.py      # MongoDB operations
├── config.py            # Configuration
├── schemas.py           # Pydantic models
└── utils.py             # Utilities

workflows/               # n8n workflow definitions
├── demo_pipeline.json
├── onboarding_pipeline.json  
└── full_pipeline.json

dataset/                 # Sample transcripts
├── demo/               # Demo call transcripts
└── onboarding/         # Onboarding call transcripts
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Start services
docker-compose up -d mongodb n8n
python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000

# Run tests (if available)
pytest
```

### Adding New Accounts
1. Add demo transcript to `dataset/demo/{account_id}_demo.txt`  
2. Add onboarding transcript to `dataset/onboarding/{account_id}_onboarding.txt`
3. Process via API or workflows

## 🔧 Configuration

### Environment Variables
```bash
# Required
GROQ_API_KEY=your_groq_api_key

# Optional (defaults shown)
GROQ_MODEL=llama3-70b-8192
MONGODB_URI=mongodb://admin:password@mongodb:27017/
MONGODB_DATABASE=agent
LOG_LEVEL=INFO
```

### MongoDB Access
```bash
# Connect to MongoDB directly
docker exec -it mongodb mongosh -u admin -p password --authenticationDatabase admin

# Use Agent database
use agent

# List accounts
db.accounts.find()

# Query specific account
db.accounts.find({"account_id": "ace_plumbing", "version": "v2"})
```

## 🚨 Troubleshooting

### Common Issues

**MongoDB Connection Errors:**
```bash
# Remove old volumes and restart
docker-compose down -v
docker-compose up -d
```

**API Errors:**
```bash
# Check logs
docker-compose logs api

# Rebuild API container
docker-compose up -d --build api
```

**n8n Workflow Issues:**
- Ensure webhooks are activated in n8n interface
- Check workflow execution logs in n8n UI
- Verify API endpoints are accessible from n8n container

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service logs  
docker-compose logs api
docker-compose logs mongodb
docker-compose logs n8n
```

## 📈 Scaling Considerations

- **MongoDB**: Configure replica sets for production
- **API**: Use multiple containers behind load balancer  
- **n8n**: Scale workflow instances for high throughput
- **AI Processing**: Consider Groq rate limits and batch processing

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Agent Pipeline** - Transforming conversations into configurations 🎯
