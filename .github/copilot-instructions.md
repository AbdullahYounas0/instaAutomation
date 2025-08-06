<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

This is a full-stack Instagram automation web application with the following structure:

## Project Overview
- **Frontend**: React TypeScript application with routing, file uploads, and real-time logging
- **Backend**: Flask Python API server with file upload handling and script management
- **Purpose**: Manage Instagram automation scripts for posting, DM campaigns, and account warmup

## Architecture
### Frontend (React + TypeScript)
- `src/components/HomePage.tsx` - Main dashboard with 3 script buttons
- `src/components/DailyPostPage.tsx` - Instagram post automation interface
- `src/components/DMAutomationPage.tsx` - DM campaign management interface  
- `src/components/WarmupPage.tsx` - Account warmup configuration interface
- Uses React Router for navigation, Axios for API calls
- Real-time log streaming and status updates

### Backend (Flask + Python)
- `backend/app.py` - Main Flask server with CORS enabled
- RESTful API endpoints for each script type
- File upload handling for Excel/CSV/media files
- Real-time logging system with WebSocket potential
- Thread-based script execution with status tracking

## Key Features
1. **Daily Post Automation**: Upload media + accounts, concurrent posting
2. **DM Automation**: AI-powered personalized messaging with DeepSeek integration
3. **Account Warmup**: Human-like behavior simulation for account trust building

## Development Guidelines
- Use TypeScript for all React components
- Follow Flask best practices for API development
- Implement proper error handling and validation
- Maintain real-time logging capabilities
- Support file uploads (Excel, CSV, images, videos)
- Ensure responsive design for mobile devices

## API Endpoints Pattern
- POST `/api/{script-type}/start` - Start script execution
- GET `/api/script/{script-id}/status` - Get script status
- GET `/api/script/{script-id}/logs` - Get real-time logs
- POST `/api/script/{script-id}/stop` - Stop running script

When working on this project, prioritize user experience, real-time feedback, and robust error handling.
