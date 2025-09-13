#!/bin/bash

# PDF Translation Platform Startup Script

echo "🚀 Starting PDF Translation Platform..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp env.example .env
    echo "📝 Please edit .env file and add your OpenAI API key"
    echo "   Then run this script again"
    exit 1
fi

# Check if OpenAI API key is set
if grep -q "your_openai_api_key_here" .env; then
    echo "⚠️  Please set your OpenAI API key in .env file"
    exit 1
fi

echo "📦 Starting infrastructure services..."
docker-compose up -d db cache

echo "⏳ Waiting for services to be healthy..."
sleep 10

echo "🔧 Starting application services..."
docker-compose up -d api worker monitor

echo "✅ Services started successfully!"
echo ""
echo "🌐 Access points:"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Celery Monitor: http://localhost:5555"
echo ""
echo "📱 To start the frontend:"
echo "   cd frontend && npm install && npm run dev"
echo ""
echo "📊 To view logs:"
echo "   docker-compose logs -f"
