#!/bin/bash

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

# Function to deploy to Vercel
deploy() {
    echo -e "${YELLOW}Deploying Nike Base Map to Vercel...${NC}"
    
    # Check if we're logged in to Vercel
    if ! vercel whoami &> /dev/null; then
        echo -e "${YELLOW}You need to log in to Vercel first.${NC}"
        vercel login
    fi
    
    # Deploy to Vercel
    if [ "$1" == "production" ]; then
        echo -e "${YELLOW}Deploying to production...${NC}"
        vercel --prod
    else
        echo -e "${YELLOW}Deploying to preview environment...${NC}"
        vercel
    fi
}

# Function to show logs
show_logs() {
    echo -e "${YELLOW}Showing logs for Nike Base Map on Vercel...${NC}"
    vercel logs
}

# Function to show help
show_help() {
    echo -e "${GREEN}Nike Missile Base Map - Vercel Deployment Script${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  deploy        - Deploy to Vercel preview environment"
    echo "  deploy:prod   - Deploy to Vercel production environment"
    echo "  logs          - Show Vercel logs"
    echo "  help          - Show this help message"
    echo ""
    echo "If no command is provided, the script will show this help message."
}

# Main script logic
case "$1" in
    deploy)
        deploy
        ;;
    deploy:prod)
        deploy "production"
        ;;
    logs)
        show_logs
        ;;
    help|"")
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac

exit 0 
