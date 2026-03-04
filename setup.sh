#!/bin/bash

# Agent Pipeline Setup Script
# This script helps you set up Agent Pipeline quickly

set -e

echo "🤖 Agent Pipeline Setup"
echo "======================"

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first:"
    echo "   https://www.docker.com/products/docker-desktop/"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Desktop which includes Compose."
    exit 1
fi

echo "✅ Docker is installed"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "✅ Docker is running"

# Check for .env file and GROQ_API_KEY
echo ""
echo "🔑 Checking API key configuration..."

if [[ ! -f .env ]]; then
    echo "⚠️  No .env file found. Creating one..."
    cat > .env << 'EOF'
# Agent Pipeline Configuration
GROQ_API_KEY=your_groq_key_here

# Optional settings (defaults shown)
GROQ_MODEL=llama3-70b-8192
MONGODB_URI=mongodb://admin:password@mongodb:27017/
MONGODB_DATABASE=agent
LOG_LEVEL=INFO
EOF
    echo "📝 Created .env file"
fi

if grep -q "your_groq_key_here" .env || ! grep -q "GROQ_API_KEY=" .env || grep -q "GROQ_API_KEY=$" .env; then
    echo ""
    echo "❌ GROQ_API_KEY not configured properly"
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
    
    echo "✅ API key saved to .env file"
fi

echo "✅ API key is configured"

# Start services
echo ""
echo "🚀 Starting Agent Pipeline services..."
echo "This may take a few minutes on first run..."

docker-compose down > /dev/null 2>&1 || true
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."

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
    echo "❌ API failed to start within 60 seconds"
    echo "Check logs with: docker-compose logs api"
    exit 1
fi

# Test services
echo "🧪 Testing services..."

# Test API
api_response=$(curl -s http://localhost:8000/health || echo "failed")
if [[ $api_response == *"healthy"* ]]; then
    echo "✅ API Server: http://localhost:8000"
else
    echo "❌ API Server: Failed to respond"
fi

# Test Database
db_response=$(curl -s http://localhost:8000/db/health || echo "failed")
if [[ $db_response == *"healthy"* ]]; then
    echo "✅ MongoDB: Connected"
else
    echo "⚠️  MongoDB: Check connection"
fi

# Check n8n
if curl -s http://localhost:5678 > /dev/null 2>&1; then
    echo "✅ n8n Workflows: http://localhost:5678"
else
    echo "⚠️  n8n Workflows: Starting up..."
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📚 Quick Commands:"
echo "   API Docs:     http://localhost:8000/docs"
echo "   n8n Flows:    http://localhost:5678"
echo "   View Logs:    docker-compose logs -f"
echo "   Stop All:     docker-compose down"
echo ""
echo "🔥 Test with sample data:"
echo "   curl -X POST http://localhost:8000/pipeline/process-all/demo"
echo ""
echo "📖 Full documentation in README.md"