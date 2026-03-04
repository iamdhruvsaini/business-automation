#!/bin/bash

# Agent Pipeline Setup Script
# This script helps you set up Agent Pipeline quickly

set -e

echo "[Agent Pipeline Setup]"
echo "======================="

# Check prerequisites
echo "[INFO] Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed. Please install Docker Desktop first:"
    echo "   https://www.docker.com/products/docker-desktop/"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "[ERROR] Docker Compose is not available. Please install Docker Desktop which includes Compose."
    exit 1
fi

echo "[OK] Docker is installed"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "[ERROR] Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "[OK] Docker is running"

# Check Python environment setup for Docker development
echo ""
echo "[INFO] Setting up Python environment for Docker development..."
echo "[INFO] You can use the following commands inside Docker containers:"
echo "   - pip install -r requirements.txt"
echo "   - uv sync (if using uv for dependency management)"
echo "   - python -m venv venv && source venv/bin/activate (for local venv)"

# Check for .env file and GROQ_API_KEY
echo ""
echo "[INFO] Checking API key configuration..."

if [[ ! -f .env ]]; then
    echo "[WARN] No .env file found. Creating one..."
    cat > .env << 'EOF'
# Agent Pipeline Configuration
GROQ_API_KEY=your_groq_key_here

# Optional settings (defaults shown)
GROQ_MODEL=llama3-70b-8192
MONGODB_URI=mongodb://admin:password@mongodb:27017/
MONGODB_DATABASE=agent
LOG_LEVEL=INFO
EOF
    echo "[OK] Created .env file"
fi

if grep -q "your_groq_key_here" .env || ! grep -q "GROQ_API_KEY=" .env || grep -q "GROQ_API_KEY=$" .env; then
    echo ""
    echo "[ERROR] GROQ_API_KEY not configured properly"
    echo ""
    echo "Please get your free Groq API key:"
    echo "1. Visit: https://console.groq.com/"
    echo "2. Sign up/login"
    echo "3. Go to API Keys section"
    echo "4. Create a new API key"
    echo "5. Copy the key (starts with 'gsk_')"
    echo ""
    read -p "Enter your Groq API key: " groq_key
    
    # Update .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/GROQ_API_KEY=.*/GROQ_API_KEY=$groq_key/" .env
    else
        # Linux
        sed -i "s/GROQ_API_KEY=.*/GROQ_API_KEY=$groq_key/" .env
    fi
    
    echo "[OK] API key saved to .env file"
fi

echo "[OK] API key is configured"

# Start services
echo ""
echo "[INFO] Starting Agent Pipeline services..."
echo "This may take a few minutes on first run..."

# Install Python dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "[INFO] Installing Python dependencies..."
    echo "[CMD] pip install -r requirements.txt"
fi

# Check for uv and sync dependencies
if [ -f "pyproject.toml" ]; then
    echo "[INFO] pyproject.toml found - you can use uv for dependency management"
    echo "[CMD] uv sync"
fi

docker-compose down > /dev/null 2>&1 || true
docker-compose up -d

echo ""
echo "[INFO] Waiting for services to start..."

# Wait for API to be ready
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        break
    fi
    attempt=$((attempt + 1))
    sleep 2
    echo -n "."
done

echo ""

if [ $attempt -eq $max_attempts ]; then
    echo "[ERROR] API failed to start within 60 seconds"
    echo "Check logs with: docker-compose logs api"
    exit 1
fi

# Test services
echo "[INFO] Testing services..."

# Test API
api_response=$(curl -s http://localhost:8000/health || echo "failed")
if [[ $api_response == *"healthy"* ]]; then
    echo "[OK] API Server: http://localhost:8000"
else
    echo "[ERROR] API Server: Failed to respond"
fi

# Test Database
db_response=$(curl -s http://localhost:8000/db/health || echo "failed")
if [[ $db_response == *"healthy"* ]]; then
    echo "[OK] MongoDB: Connected"
else
    echo "[WARN] MongoDB: Check connection"
fi

# Check n8n
if curl -s http://localhost:5678 > /dev/null 2>&1; then
    echo "[OK] n8n Workflows: http://localhost:5678"
else
    echo "[WARN] n8n Workflows: Starting up..."
fi

echo ""
echo "[SUCCESS] Setup complete!"
echo ""
echo "[Commands] Quick Commands:"
echo "   API Docs:     http://localhost:8000/docs"
echo "   n8n Flows:    http://localhost:5678"
echo "   View Logs:    docker-compose logs -f"
echo "   Stop All:     docker-compose down"
echo ""
echo "[Python] Development Commands:"
echo "   Connect to container: docker exec -it project-api-1 bash"
echo "   Install deps:         pip install -r requirements.txt"
echo "   UV sync:             uv sync"
echo "   Activate venv:        source venv/bin/activate"
echo ""
echo "[Test] Test with sample data:"
echo "   curl -X POST http://localhost:8000/pipeline/process-all/demo"
echo ""
echo "[Docs] Full documentation in README.md"