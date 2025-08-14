# Instagram Automation Platform

A comprehensive Instagram automation platform built with **FastAPI** backend and **React** frontend. This application provides Instagram warmup, DM automation, daily posting, and account management features.

> **🚀 PRODUCTION READY**: This project is now fully configured for production deployment with Docker, secure secret keys, SSL support, and enterprise-grade reliability.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Docker Deployment (Recommended)](#-docker-deployment-recommended)
- [Traditional Deployment (Alternative)](#%EF%B8%8F-traditional-deployment-alternative)
- [API Documentation](#api-documentation)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)

## ✨ Features

### 🔐 Authentication & User Management
- **JWT-based authentication** with role-based access control
- **Admin and VA user roles** with different permissions
- **User activity logging** with IP tracking and geolocation
- **Secure password hashing** using bcrypt

### 📱 Instagram Automation
- **Account Warmup**: Automated account warming with customizable actions
- **DM Automation**: Bulk direct messaging with template support
- **Daily Posting**: Scheduled content posting with visual mode
- **Account Management**: Multiple Instagram account handling

### 🌐 Web Interface
- **Modern React UI** with responsive design
- **Real-time status updates** for automation tasks
- **Interactive dashboards** for monitoring activities
- **File upload support** for bulk operations

### 🔧 Technical Features
- **FastAPI backend** with automatic API documentation
- **Background task processing** for long-running operations
- **CORS support** for cross-origin requests
- **File-based data storage** (JSON) for simplicity
- **Comprehensive error handling** and logging

## 🏗️ Architecture

```
┌─────────────────┐    HTTP/REST API    ┌─────────────────┐
│   React Frontend │ ◄─────────────────► │ FastAPI Backend │
│   (Port 3000)    │                     │   (Port 5000)   │
└─────────────────┘                     └─────────────────┘
                                                   │
                                                   ▼
                                         ┌─────────────────┐
                                         │  Data Storage   │
                                         │ (JSON Files)    │
                                         └─────────────────┘
```

## 📦 Prerequisites

### Required Software
- **Node.js** (v16 or higher) - [Download](https://nodejs.org/)
- **Python** (3.8 or higher) - [Download](https://python.org/)
- **Git** (for version control) - [Download](https://git-scm.com/)

### For Production Deployment
- **Ubuntu/Linux Server** (20.04+ recommended)
- **Nginx** (web server and reverse proxy)
- **PM2** (process manager for Node.js)
- **Domain name** with SSL certificate

## 🚀 Local Development Setup

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd instaUI2
```

### 2. Backend Setup

#### Navigate to Backend Directory
```bash
cd backend
```

#### Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Environment (Optional)
Create a `.env` file in the backend directory:
```env
SECRET_KEY=your-super-secret-jwt-key-change-in-production
PORT=5000
```

#### Start the Backend Server
```bash
# Option 1: Direct Python execution
python app.py

# Option 2: Using environment variable
PORT=5000 python app.py

# Option 3: Using uvicorn directly
uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

The backend will be available at: `http://localhost:5000`

### 3. Frontend Setup

#### Navigate to Frontend Directory (in a new terminal)
```bash
cd frontend
```

#### Install Node.js Dependencies
```bash
npm install
```

#### Start the Frontend Development Server
```bash
npm start
```

The frontend will be available at: `http://localhost:3000`

### 4. Using VS Code Tasks (Recommended)

If using VS Code, you can start both services simultaneously:

1. Open the project in VS Code
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
3. Type "Run Task" and select "Tasks: Run Task"
4. Choose "Start Full Stack Application"

This will automatically start both backend and frontend servers.

## 🐳 Docker Deployment (Recommended)

The easiest way to deploy this application is using Docker containers. This approach provides:
- ✅ Consistent environment across development and production
- ✅ Easy setup and deployment
- ✅ Automatic dependency management
- ✅ Built-in health checks and restart policies
- ✅ Isolated and secure containers

### Prerequisites
- Docker Engine 20.10 or later
- Docker Compose 2.0 or later
- At least 4GB RAM and 20GB disk space

### Quick Docker Deployment

#### 1. Clone and Setup
```bash
git clone https://github.com/AbdullahYounas0/instaAutomation.git
cd instaAutomation

# Copy and configure environment
cp .env.example .env
```

#### 2. Configure Environment Variables
Edit `.env` file with your production settings:
```bash
SECRET_KEY=your-production-secret-key-here
JWT_SECRET_KEY=your-production-jwt-secret-here
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### 3. Build and Start
```bash
# Build and start all containers
docker-compose up -d --build

# Check status
docker-compose ps
docker-compose logs
```

Your application will be available at:
- **Frontend**: http://localhost
- **Backend API**: http://localhost/api

### Docker Management Commands

Using the included Makefile for easy management:

```bash
# Start in production mode
make prod

# View logs
make logs

# Restart containers
make restart

# Create backup
make backup

# Stop everything
make down

# Clean up resources
make clean
```

### Docker Architecture

The application runs in two optimized containers:

#### Backend Container
- **Base**: Python 3.11 slim with security updates
- **Features**: FastAPI app with Playwright browsers pre-installed
- **Security**: Runs as non-root user
- **Health**: Built-in health checks on `/api/health`
- **Data**: Persistent volumes for logs, uploads, and configurations

#### Frontend Container  
- **Build Stage**: Node.js 18 for building React app
- **Runtime Stage**: Nginx Alpine for serving static files
- **Features**: Optimized production build with gzip compression
- **Proxy**: Built-in reverse proxy to backend API
- **Security**: Security headers and optimized nginx configuration

### Production SSL Setup

For production with SSL, see the detailed [Docker Deployment Guide](DOCKER_DEPLOYMENT.md) for:
- SSL certificate setup with Let's Encrypt
- Domain configuration
- Advanced nginx proxy configuration
- Production security hardening

## 🖥️ Traditional Deployment (Alternative)

If you prefer traditional deployment without Docker, you can still use the manual setup process:

```bash
# Allow SSH, HTTP, and HTTPS
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## 📚 API Documentation

### Interactive API Documentation
Once the backend is running, visit:
- **Swagger UI**: `http://localhost:5000/docs`
- **ReDoc**: `http://localhost:5000/redoc`

### Key Endpoints

#### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/verify-token` - Verify JWT token

#### User Management (Admin only)
- `GET /api/users` - Get all users
- `POST /api/users` - Create new user
- `PUT /api/users/{user_id}` - Update user
- `DELETE /api/users/{user_id}` - Delete user

#### Instagram Automation
- `GET /api/accounts` - Get Instagram accounts
- `POST /api/accounts` - Add Instagram account
- `POST /api/warmup/start` - Start account warmup
- `POST /api/dm/send` - Send DM campaign
- `POST /api/daily-post/start` - Start daily posting

#### System
- `GET /api/health` - Health check
- `GET /api/scripts` - Get running scripts
- `POST /api/scripts/stop` - Stop running script

## 📖 Usage Guide

### Default Login Credentials
- **Username**: `admin`
- **Password**: `admin123`

**⚠️ Important**: Change the default admin password immediately after first login!

### Basic Workflow

1. **Login** with admin credentials
2. **Add Instagram accounts** in the Accounts section
3. **Create VA users** if needed (Virtual Assistants)
4. **Configure automation settings** for each account
5. **Start automation tasks** (warmup, DM, posting)
6. **Monitor progress** in the dashboard

### Account Warmup
- Gradual increase in account activity
- Follows, likes, comments, and story views
- Customizable warmup schedules
- Prevents account restrictions

### DM Automation
- Bulk messaging to targeted users
- Template-based messages with personalization
- Rate limiting to avoid blocks
- CSV import for recipient lists

### Daily Posting
- Scheduled content publishing
- Visual mode for story posting
- Bulk upload support
- Automatic scheduling

## 🔧 Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check if port is in use
netstat -tulpn | grep :5000

# Kill process using the port
sudo kill -9 $(lsof -t -i:5000)

# Check Python dependencies
pip install -r requirements.txt
```

#### Frontend Build Fails
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear npm cache
npm cache clean --force
```

#### Authentication Issues
```bash
# Check JWT secret key configuration
# Verify users.json file exists and is readable
# Check token expiration settings
```

#### Permission Errors
```bash
# Set proper file permissions
sudo chown -R www-data:www-data /var/www/instagram-automation
sudo chmod -R 755 /var/www/instagram-automation
```

### Logging and Debugging

#### Backend Logs
```bash
# PM2 logs
pm2 logs instagram-automation-backend

# Direct Python logs
tail -f backend/logs/app.log
```

#### Nginx Logs
```bash
# Access logs
sudo tail -f /var/log/nginx/access.log

# Error logs
sudo tail -f /var/log/nginx/error.log
```

#### Check Service Status
```bash
# PM2 status
pm2 status

# Nginx status
sudo systemctl status nginx
```

## 📁 Project Structure

```
instaUI2/
├── README.md                          # This file
├── .gitignore                         # Git ignore rules
├── .env.example                       # Environment variables template
├── .vscode/                           # VS Code configuration
│   └── tasks.json                     # Development tasks
├── backend/                           # FastAPI backend
│   ├── app.py                         # Main FastAPI application
│   ├── auth.py                        # Authentication module
│   ├── requirements.txt               # Python dependencies
│   ├── users.json                     # User data storage
│   ├── activity_logs.json             # Activity logs
│   ├── instagram_accounts.json        # Instagram accounts
│   ├── instagram_warmup.py            # Warmup automation
│   ├── instagram_dm_automation.py     # DM automation
│   ├── instagram_daily_post.py        # Daily posting
│   └── instagram_accounts.py          # Account management
└── frontend/                          # React frontend
    ├── public/                        # Static assets
    ├── src/                           # Source code
    │   ├── components/                # React components
    │   ├── pages/                     # Page components
    │   ├── config/                    # Configuration
    │   └── services/                  # API services
    ├── package.json                   # Node.js dependencies
    └── build/                         # Production build (generated)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review the API documentation at `/docs`

---

**Made with ❤️ for Instagram automation**
