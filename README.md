# Instagram Automation Platform

A comprehensive Instagram automation platform built with **FastAPI** backend and **React** frontend. This application provides Instagram warmup, DM automation, daily posting, and account management features.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Production Deployment](#production-deployment)
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

## 🌐 Production Deployment

### 1. Server Preparation

#### Update System Packages
```bash
sudo apt update && sudo apt upgrade -y
```

#### Install Required Software
```bash
# Install Node.js (using NodeSource repository)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install Nginx
sudo apt install nginx -y

# Install PM2 globally
sudo npm install -g pm2
```

### 2. Application Deployment

#### Clone and Setup Backend
```bash
# Clone the repository
git clone <your-repository-url> /var/www/instagram-automation
cd /var/www/instagram-automation

# Setup Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Create production environment file
cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
PORT=5000
EOF
```

#### Setup Frontend
```bash
cd ../frontend

# Install dependencies
npm install

# Build for production
npm run build
```

### 3. Process Management with PM2

#### Create PM2 Configuration
Create `ecosystem.config.js` in the project root:
```javascript
module.exports = {
  apps: [
    {
      name: 'instagram-automation-backend',
      cwd: '/var/www/instagram-automation/backend',
      script: 'app.py',
      interpreter: '/var/www/instagram-automation/venv/bin/python',
      env: {
        PORT: 5000,
        NODE_ENV: 'production'
      },
      error_file: '/var/log/pm2/instagram-automation-backend-error.log',
      out_file: '/var/log/pm2/instagram-automation-backend-out.log',
      log_file: '/var/log/pm2/instagram-automation-backend.log'
    }
  ]
};
```

#### Start with PM2
```bash
# Create log directory
sudo mkdir -p /var/log/pm2

# Start the application
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $(whoami) --hp $(eval echo ~$(whoami))
```

### 4. Nginx Configuration

#### Create Nginx Configuration
```bash
sudo tee /etc/nginx/sites-available/instagram-automation << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Serve React frontend
    location / {
        root /var/www/instagram-automation/frontend/build;
        index index.html index.htm;
        try_files \$uri \$uri/ /index.html;
    }

    # Proxy API requests to FastAPI backend
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    # Handle large file uploads
    client_max_body_size 50M;
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/instagram-automation /etc/nginx/sites-enabled/

# Test and reload Nginx
sudo nginx -t
sudo systemctl reload nginx
```

### 5. SSL Certificate (Recommended)

#### Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
```

#### Obtain SSL Certificate
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### 6. Firewall Configuration

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
