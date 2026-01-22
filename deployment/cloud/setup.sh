#!/bin/bash

# setup.sh - Install PM2 and initialize cloud deployment
# Usage: ./setup.sh [--test]

set -e

echo "========================================="
echo "Cloud Agent Setup"
echo "========================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed"
    echo "Please install Node.js 20+ before running this script"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "ERROR: npm is not installed"
    exit 1
fi

# Check Node.js version (require 20+)
NODE_VERSION=$(node --version | cut -d'.' -f1 | sed 's/v//')
if [ "$NODE_VERSION" -lt 20 ]; then
    echo "ERROR: Node.js 20+ required (found: $(node --version))"
    exit 1
fi

echo "✓ Node.js $(node --version) detected"

# Install PM2 globally if not already installed
if ! command -v pm2 &> /dev/null; then
    echo "Installing PM2..."
    npm install -g pm2
    if [ $? -eq 0 ]; then
        echo "✓ PM2 installed successfully"
    else
        echo "ERROR: Failed to install PM2"
        exit 1
    fi
else
    echo "✓ PM2 $(pm2 --version) already installed"
fi

# Install project dependencies
echo "Installing project dependencies..."
npm install

# Create necessary config directories
mkdir -p config addons logs

# Copy .env.example to .env if .env doesn't exist
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ Created .env from .env.example"
        echo "⚠ WARNING: Please edit .env with your actual credentials"
    else
        echo "ERROR: .env.example not found"
        exit 1
    fi
else
    echo "✓ .env already exists"
fi

# Test PM2 ecosystem configuration
echo ""
echo "Testing PM2 ecosystem configuration..."
if [ "$1" = "--test" ]; then
    echo "Testing PM2 ecosystem with dry-run..."
    pm2 validate ecosystem.config.js
    if [ $? -eq 0 ]; then
        echo "✓ PM2 ecosystem configuration is valid"
    else
        echo "ERROR: PM2 ecosystem configuration has issues"
        exit 1
    fi
else
    echo "Use './setup.sh --test' to validate ecosystem.config.js"
fi

# Save PM2 configuration
pm2 save

# Setup PM2 startup script
echo ""
echo "Note: To enable PM2 startup on boot, run:"
echo "  pm2 startup"
echo "  # Follow the instructions from PM2"
echo ""
echo "========================================="
echo "Setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env with your credentials"
echo "2. Run: docker-compose up -d (for Odoo)"
echo "3. Run: pm2 start ecosystem.config.js"
echo "4. Check status: pm2 status"
