#!/bin/bash

# Vercel deployment script for Nike Missile Base Map

set -e

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${RED}Vercel CLI is not installed. Please install it first with 'npm i -g vercel'.${NC}"
    exit 1
fi

# Function to display usage information
function show_usage {
    echo -e "${GREEN}Nike Missile Base Map - Vercel Deployment Script${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  deploy         Deploy to preview environment"
    echo "  deploy:prod    Deploy to production"
    echo "  logs           View deployment logs"
    echo "  help           Show this help message"
    echo ""
}

# Process command
case "$1" in
    deploy)
        echo -e "${YELLOW}Deploying Nike Base Map to Vercel...${NC}"
        echo -e "${YELLOW}Deploying to preview environment...${NC}"
        vercel
        ;;
    deploy:prod)
        echo -e "${YELLOW}Deploying Nike Base Map to Vercel...${NC}"
        echo -e "${YELLOW}Deploying to production...${NC}"
        vercel --prod
        ;;
    logs)
        echo -e "${YELLOW}Showing logs for Nike Base Map on Vercel...${NC}"
        echo -e "${YELLOW}Fetching logs...${NC}"
        vercel logs
        ;;
    help|*)
        show_usage
        ;;
esac

exit 0 
