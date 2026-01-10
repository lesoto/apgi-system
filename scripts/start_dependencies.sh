#!/bin/bash

# APGI System Dependency Setup Script
# This script sets up and starts the required database dependencies

set -e

echo "🚀 Starting APGI System Dependencies..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Start the dependencies
echo "📦 Starting PostgreSQL and Redis containers..."
docker-compose up -d postgres redis

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
sleep 10

# Check if PostgreSQL is ready
echo "🔍 Checking PostgreSQL connection..."
until docker-compose exec postgres pg_isready -U apgi -d apgi_api; do
    echo "PostgreSQL is unavailable - sleeping..."
    sleep 2
done

# Check if Redis is ready
echo "🔍 Checking Redis connection..."
until docker-compose exec redis redis-cli ping; do
    echo "Redis is unavailable - sleeping..."
    sleep 2
done

echo "✅ Dependencies are ready!"
echo ""
echo "📊 Database Info:"
echo "  PostgreSQL: localhost:5432"
echo "  Redis: localhost:6379"
echo ""
echo "🔐 Connection Details:"
echo "  Database: apgi_api"
echo "  Username: apgi"
echo "  Password: apgi_password"
echo ""
echo "🎯 You can now start the API server with:"
echo "  python -m api.main"
echo ""
echo "🛑 To stop dependencies, run:"
echo "  docker-compose down"
