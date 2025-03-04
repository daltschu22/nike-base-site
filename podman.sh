#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Define container name
CONTAINER_NAME="nike-base-map"

# Check if Podman is installed
if ! command -v podman &> /dev/null; then
    echo -e "${RED}Podman is not installed. Please install Podman first.${NC}"
    exit 1
fi

# Function to start the container
start_container() {
    echo -e "${YELLOW}Starting Nike Base Map with Podman...${NC}"
    
    # Clean up any existing CNI configurations that might cause warnings
    if [ -d "$HOME/.config/cni/net.d" ]; then
        echo "Cleaning up existing CNI configurations..."
        rm -f $HOME/.config/cni/net.d/*_default.conflist
    fi
    
    # Check if the container already exists and is running
    if podman ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${YELLOW}Container is already running.${NC}"
        echo -e "${GREEN}The application is running at: http://localhost:5000${NC}"
        return 0
    fi
    
    # Check if the container exists but is stopped
    if podman ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        echo "Container exists but is not running. Removing it..."
        podman rm -f ${CONTAINER_NAME} > /dev/null
    fi
    
    # Build the image
    echo "Building the image..."
    podman build -t nike-base-map:latest .
    
    # Run the container
    echo "Starting the container..."
    podman run --name ${CONTAINER_NAME} -d -p 5000:5000 -v "$(pwd):/app:Z" nike-base-map:latest
    
    # Check if the container started successfully
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Container started successfully!${NC}"
        echo -e "${GREEN}The application is now running at: http://localhost:5000${NC}"
        echo -e "To view logs: ${YELLOW}$0 logs${NC}"
        echo -e "To stop the container: ${YELLOW}$0 stop${NC}"
    else
        echo -e "${RED}Failed to start the container. Please check the error messages above.${NC}"
        exit 1
    fi
}

# Function to stop the container
stop_container() {
    echo -e "${YELLOW}Stopping Nike Base Map...${NC}"
    
    # Check if the container exists
    if podman ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        # Stop and remove the container
        echo "Stopping and removing the container..."
        podman stop ${CONTAINER_NAME} > /dev/null
        podman rm ${CONTAINER_NAME} > /dev/null
        
        # Check if the container was removed successfully
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Container stopped and removed successfully!${NC}"
            
            # Clean up CNI configurations
            if [ -d "$HOME/.config/cni/net.d" ]; then
                echo "Cleaning up CNI configurations..."
                rm -f $HOME/.config/cni/net.d/${CONTAINER_NAME}_default.conflist
            fi
        else
            echo -e "${RED}Failed to stop or remove the container.${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}Container ${CONTAINER_NAME} is not running or does not exist.${NC}"
    fi
}

# Function to show container logs
show_logs() {
    echo -e "${YELLOW}Showing logs for Nike Base Map...${NC}"
    
    # Check if the container is running
    if podman ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        echo "Press Ctrl+C to exit logs (the container will continue running)"
        podman logs -f ${CONTAINER_NAME}
    else
        echo -e "${RED}Container ${CONTAINER_NAME} is not running.${NC}"
        echo -e "Start the container with: ${YELLOW}$0 start${NC}"
    fi
}

# Function to show container status
show_status() {
    # Check if the container is running
    if podman ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${GREEN}Container ${CONTAINER_NAME} is running.${NC}"
        echo -e "The application is available at: ${GREEN}http://localhost:5000${NC}"
        echo -e "Container ID: $(podman ps --filter name=${CONTAINER_NAME} --format '{{.ID}}')"
        echo -e "Image: $(podman ps --filter name=${CONTAINER_NAME} --format '{{.Image}}')"
        echo -e "Created: $(podman ps --filter name=${CONTAINER_NAME} --format '{{.Created}}')"
    else
        echo -e "${YELLOW}Container ${CONTAINER_NAME} is not running.${NC}"
        
        # Check if the container exists but is stopped
        if podman ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
            echo -e "${YELLOW}Container exists but is stopped.${NC}"
        else
            echo -e "${YELLOW}Container does not exist.${NC}"
        fi
    fi
}

# Function to clean up CNI configurations
cleanup_cni() {
    echo -e "${YELLOW}Cleaning up CNI configurations...${NC}"
    
    if [ -d "$HOME/.config/cni/net.d" ]; then
        echo "Removing CNI configuration files..."
        rm -f $HOME/.config/cni/net.d/*.conflist
        echo -e "${GREEN}CNI configurations cleaned up successfully!${NC}"
    else
        echo "No CNI configuration directory found."
    fi
}

# Function to show help
show_help() {
    echo -e "${GREEN}Nike Missile Base Map - Podman Script${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start    - Build and start the container"
    echo "  stop     - Stop and remove the container"
    echo "  restart  - Restart the container"
    echo "  logs     - Show container logs"
    echo "  status   - Show container status"
    echo "  cleanup  - Clean up CNI configurations"
    echo "  help     - Show this help message"
    echo ""
    echo "If no command is provided, the script will show this help message."
}

# Main script logic
case "$1" in
    start)
        start_container
        ;;
    stop)
        stop_container
        ;;
    restart)
        stop_container
        start_container
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    cleanup)
        cleanup_cni
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
