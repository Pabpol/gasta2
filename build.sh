#!/bin/bash

# Railway build script for Gasta2 monorepo
echo "🏗️  Starting Gasta2 build process..."

# Install Node.js if not available
if ! command -v npm &> /dev/null; then
    echo "⚠️  Node.js not found, installing..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend_dashboard
npm ci

# Build frontend for production
echo "🏗️  Building frontend..."
npm run build

# Move built files to backend static directory
echo "📁 Moving built files to backend..."
cd ..
rm -rf backend_gastos/static/*
# SvelteKit builds to .svelte-kit/output/client
cp -r frontend_dashboard/.svelte-kit/output/client/* backend_gastos/static/

# Install backend dependencies
echo "🐍 Installing backend dependencies..."
cd backend_gastos
# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

echo "✅ Build process completed!"
echo "Frontend built and copied to backend/static/"
echo "Backend dependencies installed"
