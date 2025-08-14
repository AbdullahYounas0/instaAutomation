# Instagram Automation Docker Management
# Use 'make help' to see available commands

.PHONY: help build up down logs restart clean backup restore

# Default target
help:
	@echo "Instagram Automation Docker Commands:"
	@echo ""
	@echo "  build       - Build Docker images"
	@echo "  up          - Start containers in detached mode"
	@echo "  down        - Stop and remove containers"
	@echo "  logs        - View container logs"
	@echo "  restart     - Restart all containers"
	@echo "  clean       - Remove containers, networks, and unused images"
	@echo "  backup      - Create backup of persistent data"
	@echo "  restore     - Restore from backup (requires BACKUP_FILE variable)"
	@echo "  dev         - Start in development mode (with logs)"
	@echo "  prod        - Start in production mode"
	@echo "  prod-ssl    - Start in production mode with SSL"
	@echo "  status      - Show container status"
	@echo "  setup-ssl   - Setup SSL certificates with Let's Encrypt"
	@echo "  deploy-prod - Full production deployment with updates"
	@echo ""
	@echo "Examples:"
	@echo "  make build"
	@echo "  make prod"
	@echo "  make setup-ssl"
	@echo "  make prod-ssl"
	@echo "  make backup"
	@echo "  make restore BACKUP_FILE=backup-20250815.tar.gz"

# Build Docker images
build:
	@echo "Building Docker images..."
	docker-compose build

# Start containers in detached mode
up:
	@echo "Starting containers..."
	docker-compose up -d

# Stop and remove containers
down:
	@echo "Stopping containers..."
	docker-compose down

# View container logs
logs:
	docker-compose logs -f

# Restart all containers
restart:
	@echo "Restarting containers..."
	docker-compose restart

# Development mode - start with logs visible
dev:
	@echo "Starting in development mode..."
	docker-compose up --build

# Production mode - start detached with production config
prod: build
	@echo "Starting in production mode..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Containers started. Use 'make logs' to view logs."
	@echo "Application available at http://localhost"

# Production mode with SSL
prod-ssl: build
	@echo "Starting in production mode with SSL..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Production containers with SSL started."
	@echo "Application available at https://wdyautomation.shop"

# Show container status
status:
	@echo "Container Status:"
	docker-compose ps
	@echo ""
	@echo "Resource Usage:"
	docker stats --no-stream

# Clean up containers, networks, and unused images
clean:
	@echo "Cleaning up Docker resources..."
	docker-compose down -v --remove-orphans
	docker system prune -f
	@echo "Cleanup complete."

# Create backup of persistent data
backup:
	@echo "Creating backup..."
	@mkdir -p backups
	tar -czf backups/backup-$(shell date +%Y%m%d-%H%M%S).tar.gz \
		backend/logs \
		backend/uploads \
		backend/instagram_cookies \
		backend/browser_profiles \
		backend/users.json \
		backend/instagram_accounts.json \
		backend/proxy_assignments.json \
		backend/activity_logs.json \
		.env 2>/dev/null || true
	@echo "Backup created in backups/ directory"

# Restore from backup
restore:
ifndef BACKUP_FILE
	@echo "Error: Please specify BACKUP_FILE"
	@echo "Usage: make restore BACKUP_FILE=backup-20250815.tar.gz"
	@exit 1
endif
	@echo "Stopping containers..."
	docker-compose down
	@echo "Restoring backup: $(BACKUP_FILE)"
	tar -xzf $(BACKUP_FILE)
	@echo "Starting containers..."
	docker-compose up -d
	@echo "Restore complete."

# Update containers with latest images
update:
	@echo "Updating containers..."
	docker-compose pull
	docker-compose up -d --build
	@echo "Update complete."

# View backend logs specifically
backend-logs:
	docker-compose logs -f backend

# View frontend logs specifically
frontend-logs:
	docker-compose logs -f frontend

# Execute bash in backend container
backend-shell:
	docker-compose exec backend bash

# Execute sh in frontend container
frontend-shell:
	docker-compose exec frontend sh

# Check health of containers
health:
	@echo "Backend Health:"
	@curl -f http://localhost:5000/api/health 2>/dev/null || echo "Backend unhealthy"
	@echo ""
	@echo "Frontend Health:"
	@curl -f http://localhost/ >/dev/null 2>&1 && echo "Frontend healthy" || echo "Frontend unhealthy"

# Generate new secret keys
generate-secrets:
	@echo "SECRET_KEY=$(shell openssl rand -hex 32)"
	@echo "JWT_SECRET_KEY=$(shell openssl rand -hex 32)"

# Setup SSL certificates (requires domain to be pointed to server)
setup-ssl:
	@echo "Setting up SSL certificates..."
	sudo certbot certonly --standalone -d wdyautomation.shop -d www.wdyautomation.shop
	@echo "SSL certificates installed. Now run 'make prod-ssl' to start with SSL"

# Deploy to production (full deployment)
deploy-prod:
	@echo "Deploying to production..."
	git pull origin main
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Production deployment complete!"
