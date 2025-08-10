#!/bin/bash

# Instagram Automation Server Management Script
# Use this script to manage your deployed application

APP_DIR="/var/www/instaAutomation"
DOMAIN="wdyautomation.shop"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_usage() {
    echo "Usage: ./manage.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     - Start all services"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  status    - Show service status"
    echo "  logs      - Show application logs"
    echo "  update    - Pull latest code and restart"
    echo "  ssl       - Setup SSL certificate"
    echo "  backup    - Create backup of application data"
    echo "  monitor   - Show real-time logs"
}

case "$1" in
    "start")
        echo -e "${BLUE}Starting Instagram Automation services...${NC}"
        cd $APP_DIR
        pm2 start ecosystem.config.js
        sudo systemctl start nginx
        echo -e "${GREEN}Services started successfully!${NC}"
        ;;
    
    "stop")
        echo -e "${YELLOW}Stopping Instagram Automation services...${NC}"
        pm2 stop all
        echo -e "${GREEN}Services stopped successfully!${NC}"
        ;;
    
    "restart")
        echo -e "${BLUE}Restarting Instagram Automation services...${NC}"
        cd $APP_DIR
        pm2 restart all
        sudo systemctl reload nginx
        echo -e "${GREEN}Services restarted successfully!${NC}"
        ;;
    
    "status")
        echo -e "${BLUE}Service Status:${NC}"
        pm2 status
        echo ""
        echo -e "${BLUE}Nginx Status:${NC}"
        sudo systemctl status nginx --no-pager -l
        ;;
    
    "logs")
        echo -e "${BLUE}Application Logs:${NC}"
        pm2 logs --lines 50
        ;;
    
    "update")
        echo -e "${BLUE}Updating application...${NC}"
        cd $APP_DIR
        
        # Stop services
        pm2 stop all
        
        # Pull latest code
        git pull origin main
        
        # Update backend dependencies
        cd backend
        source venv/bin/activate
        pip install -r requirements.txt
        cd ..
        
        # Update and rebuild frontend
        cd frontend
        npm install
        npm run build
        cd ..
        
        # Restart services
        pm2 restart all
        
        echo -e "${GREEN}Application updated successfully!${NC}"
        ;;
    
    "ssl")
        echo -e "${BLUE}Setting up SSL certificate...${NC}"
        sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN
        echo -e "${GREEN}SSL certificate setup completed!${NC}"
        ;;
    
    "backup")
        BACKUP_DIR="/var/backups/insta-automation"
        BACKUP_FILE="insta-automation-$(date +%Y%m%d-%H%M%S).tar.gz"
        
        echo -e "${BLUE}Creating backup...${NC}"
        sudo mkdir -p $BACKUP_DIR
        
        cd /var/www
        sudo tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
            --exclude='instaAutomation/node_modules' \
            --exclude='instaAutomation/backend/venv' \
            --exclude='instaAutomation/.git' \
            instaAutomation/
        
        echo -e "${GREEN}Backup created: $BACKUP_DIR/$BACKUP_FILE${NC}"
        ;;
    
    "monitor")
        echo -e "${BLUE}Real-time monitoring (Press Ctrl+C to exit)...${NC}"
        pm2 logs --raw | grep -E "(error|Error|ERROR|warn|Warn|WARN|info|Info|INFO)"
        ;;
    
    *)
        print_usage
        ;;
esac
