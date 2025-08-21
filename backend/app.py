"""
FastAPI Instagram Automation Backend
Converted from Flask to FastAPI for better performance and async support
"""

from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form, Request, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import json
import uuid
import logging
import asyncio
import threading
import time as time_module
import tempfile
import atexit
import traceback
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import custom modules
from auth import (
    user_manager, 
    verify_token_dependency, 
    admin_required_dependency,
    log_user_activity
)
from instagram_accounts import instagram_accounts_manager
from proxy_manager import proxy_manager
from instagram_daily_post import run_daily_post_automation
from instagram_dm_automation import run_dm_automation
from instagram_warmup import run_warmup_automation

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Instagram Automation API",
    description="FastAPI backend for Instagram automation scripts",
    version="2.0.0"
)

# CORS Configuration
def get_allowed_origins():
    """Get allowed origins from environment or use defaults"""
    env_origins = os.environ.get('CORS_ORIGINS', '')
    if env_origins:
        return [origin.strip() for origin in env_origins.split(',') if origin.strip()]
    else:
        return [
            'http://localhost:3000',
            'http://127.0.0.1:3000',
            'http://localhost:8080',
            'http://127.0.0.1:8080',
            'https://instaui.sitetostart.com',
            'https://www.instaui.sitetostart.com'
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "Cache-Control",
        "Pragma"
    ],
)

# Configuration
LOGS_FOLDER = 'logs'
ALLOWED_EXTENSIONS = {
    'images': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'},
    'videos': {'mp4', 'mov', 'avi', 'mkv', 'webm', 'm4v'},
    'files': {'csv', 'xlsx', 'xls', 'txt'}
}

# Create necessary directories
os.makedirs(LOGS_FOLDER, exist_ok=True)

# Global variables to track running scripts
active_scripts = {}
script_logs = {}
script_stop_flags = {}
script_temp_files = {}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenRequest(BaseModel):
    token: str

class UserCreate(BaseModel):
    name: str
    username: str
    password: str
    role: str = "va"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class StopScriptRequest(BaseModel):
    reason: str = "Script stopped by user"

# Utility Functions
def cleanup_temp_files(script_id):
    """Clean up temporary files for a specific script"""
    if script_id in script_temp_files:
        for file_path in script_temp_files[script_id]:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.error(f"Error cleaning up temporary file {file_path}: {e}")
        del script_temp_files[script_id]

def cleanup_all_temp_files():
    """Clean up all temporary files on shutdown"""
    for script_id in list(script_temp_files.keys()):
        cleanup_temp_files(script_id)

# Register cleanup function
atexit.register(cleanup_all_temp_files)

def save_temp_file(file: UploadFile, script_id: str, prefix: str = ""):
    """Save uploaded file to temporary location and track it"""
    if script_id not in script_temp_files:
        script_temp_files[script_id] = []
    
    # Create temporary file with appropriate extension
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ''
    temp_fd, temp_path = tempfile.mkstemp(suffix=file_extension, prefix=f"{prefix}_{script_id}_")
    
    try:
        # Save file to temporary location
        with os.fdopen(temp_fd, 'wb') as temp_file:
            content = file.file.read()
            temp_file.write(content)
        
        # Track the temporary file
        script_temp_files[script_id].append(temp_path)
        return temp_path
    except Exception as e:
        # Clean up on error
        try:
            os.close(temp_fd)
            os.remove(temp_path)
        except:
            pass
        raise e

def allowed_file(filename: str, file_type: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS.get(file_type, set())

def generate_script_id() -> str:
    """Generate unique script ID"""
    return str(uuid.uuid4())

def log_script_message(script_id: str, message: str, level: str = "INFO"):
    """Log message for specific script"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    
    if script_id not in script_logs:
        script_logs[script_id] = []
    
    script_logs[script_id].append(log_entry)
    
    # Keep only last 1000 logs per script
    if len(script_logs[script_id]) > 1000:
        script_logs[script_id] = script_logs[script_id][-1000:]

# Health and Debug Endpoints
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/debug")
async def debug_endpoint(request: Request):
    """Debug endpoint to check server status"""
    return {
        "status": "Server is running",
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "available_endpoints": [
            "/api/health",
            "/api/debug", 
            "/api/cors-test",
            "/api/auth/login"
        ]
    }

@app.options("/api/cors-test")
@app.get("/api/cors-test")
@app.post("/api/cors-test")
async def cors_test(request: Request):
    """CORS test endpoint to verify CORS configuration"""
    try:
        return {
            "status": "CORS working",
            "method": request.method,
            "origin": request.headers.get('Origin', 'No origin header'),
            "user_agent": request.headers.get('User-Agent', 'No user agent'),
            "timestamp": datetime.now().isoformat(),
            "server_info": {
                "fastapi_version": "0.104.1",
                "endpoint_working": True
            },
            "cors_config": {
                "allowed_origins": get_allowed_origins(),
                "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
                "supports_credentials": True
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error": str(e),
                "method": request.method,
                "timestamp": datetime.now().isoformat()
            }
        )

# Authentication Endpoints
@app.post("/api/auth/login")
async def login(login_request: LoginRequest, request: Request):
    """Login endpoint for both admin and VA users"""
    try:
        client_ip = request.client.host if request.client else 'unknown'
        result = user_manager.authenticate_user(login_request.username, login_request.password)
        
        if result['success']:
            # Log successful login with IP
            user_id = result['user']['user_id']
            log_user_activity('login', f"Successful login from {client_ip}", user_id, client_ip)
            return result
        else:
            # Log failed login attempt
            log_user_activity('failed_login', f"Failed login attempt for {login_request.username} from {client_ip}", ip_address=client_ip)
            raise HTTPException(status_code=401, detail=result)
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Login error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.post("/api/auth/verify-token")
async def verify_token(token_request: TokenRequest):
    """Verify JWT token"""
    try:
        result = user_manager.verify_token(token_request.token)
        if not result['success']:
            raise HTTPException(status_code=401, detail=result)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.post("/api/auth/logout")
async def logout(current_user: dict = Depends(verify_token_dependency)):
    """Logout endpoint"""
    try:
        log_user_activity('logout', f"User {current_user['username']} logged out", current_user['user_id'])
        return {'success': True, 'message': 'Logged out successfully'}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

# Daily Post Endpoints
@app.post("/api/daily-post/start")
async def start_daily_post(
    background_tasks: BackgroundTasks,
    account_ids: str = Form(...),
    media_file: UploadFile = File(...),
    caption: str = Form(""),
    auto_generate_caption: bool = Form(True),
    current_user: dict = Depends(verify_token_dependency)
):
    """Start Instagram Daily Post script"""
    script_id = generate_script_id()
    
    try:
        # Parse account IDs
        try:
            account_ids_list = json.loads(account_ids)
            if not isinstance(account_ids_list, list) or len(account_ids_list) == 0:
                raise HTTPException(status_code=400, detail={"error": "Invalid account IDs format"})
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail={"error": "Invalid account IDs format"})
        
        # Get selected accounts from the accounts manager
        selected_accounts = instagram_accounts_manager.get_accounts_by_ids(account_ids_list)
        if len(selected_accounts) == 0:
            raise HTTPException(status_code=400, detail={"error": "No valid accounts found"})
        
        # Check media file type
        is_image = allowed_file(media_file.filename, 'images')
        is_video = allowed_file(media_file.filename, 'videos')
        
        if not (is_image or is_video):
            raise HTTPException(status_code=400, detail={"error": "Invalid media file format. Use supported image/video formats"})
        
        # Save uploaded media file to temporary location
        media_path = save_temp_file(media_file, script_id, "media")
        
        # Create temporary accounts file with selected accounts
        accounts_data = []
        for account in selected_accounts:
            accounts_data.append({
                'Username': account['username'],
                'Password': account['password']
            })
        
        # Save accounts to temporary CSV file
        accounts_df = pd.DataFrame(accounts_data)
        accounts_path = f"temp_accounts_{script_id}.csv"
        accounts_df.to_csv(accounts_path, index=False)
        
        # Track the temporary accounts file
        if script_id not in script_temp_files:
            script_temp_files[script_id] = []
        script_temp_files[script_id].append(accounts_path)
        
        # Initialize script tracking
        active_scripts[script_id] = {
            "type": "daily_post",
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "user_id": current_user.get('user_id', 'system'),
            "config": {
                "accounts_file": accounts_path,
                "media_file": media_path,
                "caption": caption,
                "concurrent_accounts": len(selected_accounts),
                "auto_generate_caption": auto_generate_caption,
                "is_video": is_video,
                "selected_account_ids": account_ids_list
            }
        }
        
        # Initialize stop flag
        script_stop_flags[script_id] = False
        
        log_script_message(script_id, f"Daily Post script started with {len(selected_accounts)} accounts")
        log_script_message(script_id, f"Media file: {media_file.filename} ({'Video' if is_video else 'Image'})")
        
        # Start the script in background
        background_tasks.add_task(run_daily_post_script, script_id)
        
        return {
            "script_id": script_id,
            "status": "started",
            "message": "Daily post script initiated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting daily post script: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

async def run_daily_post_script(script_id: str):
    """Run the actual daily post script"""
    try:
        config = active_scripts[script_id]["config"]
        
        # Create log callback function
        def log_callback(message, level="INFO"):
            log_script_message(script_id, message, level)
        
        # Create stop callback function
        def stop_callback():
            return script_stop_flags.get(script_id, False)
        
        log_script_message(script_id, "Starting Instagram Daily Post automation...")
        
        # Run the automation function
        success = await run_daily_post_automation(
            script_id=script_id,
            accounts_file=config['accounts_file'],
            media_file=config['media_file'],
            concurrent_accounts=config['concurrent_accounts'],
            caption=config.get('caption', ''),
            auto_generate_caption=config.get('auto_generate_caption', True),
            log_callback=log_callback,
            stop_callback=stop_callback
        )
        
        if success:
            active_scripts[script_id]["status"] = "completed"
            active_scripts[script_id]["end_time"] = datetime.now().isoformat()
            log_script_message(script_id, "Daily post script completed successfully!", "SUCCESS")
        else:
            active_scripts[script_id]["status"] = "error"
            active_scripts[script_id]["end_time"] = datetime.now().isoformat()
            active_scripts[script_id]["error"] = "Script execution failed"
            log_script_message(script_id, "Daily post script failed", "ERROR")
        
    except Exception as e:
        active_scripts[script_id]["status"] = "error"
        active_scripts[script_id]["end_time"] = datetime.now().isoformat()
        active_scripts[script_id]["error"] = str(e)
        log_script_message(script_id, f"Script error: {e}", "ERROR")
        traceback.print_exc()
    finally:
        # Clean up temporary files
        cleanup_temp_files(script_id)

# DM Automation Endpoints

# Spintax Preview Endpoint
@app.post("/api/generate-spintax-previews")
async def generate_spintax_previews(
    request: Request,
    current_user: dict = Depends(verify_token_dependency)
):
    """Generate 3 spintax preview variations from a prompt"""
    try:
        body = await request.json()
        prompt = body.get('prompt', '').strip()
        
        if not prompt:
            raise HTTPException(status_code=400, detail={"error": "Prompt is required"})
        
        # Import spintax parser
        from instagram_dm_automation import SpintaxParser
        
        # Generate 3 different variations
        previews = []
        max_attempts = 20  # Try up to 20 times to get 3 unique variations
        attempt = 0
        
        while len(previews) < 3 and attempt < max_attempts:
            variation = SpintaxParser.parse(prompt)
            if variation not in previews:  # Only add unique variations
                previews.append(variation)
            attempt += 1
        
        # If we couldn't get 3 unique variations, fill with the ones we have
        while len(previews) < 3:
            previews.append(SpintaxParser.parse(prompt))
        
        return {
            "success": True,
            "previews": previews,
            "original_prompt": prompt
        }
        
    except Exception as e:
        logger.error(f"Error generating spintax previews: {e}")
        return {
            "success": False,
            "error": str(e),
            "previews": []
        }

@app.post("/api/generate-ai-spintax-samples")
async def generate_ai_spintax_samples(
    request: Request,
    current_user: dict = Depends(verify_token_dependency)
):
    """Generate template-based spintax samples (AI functionality removed)"""
    try:
        body = await request.json()
        prompt = body.get('prompt', '').strip()
        count = body.get('count', 3)
        
        if not prompt:
            raise HTTPException(status_code=400, detail={"error": "Prompt is required"})
        
        # Import required modules
        from instagram_dm_automation import SpintaxParser
        
        # Generate template-based spintax variations (since AI is removed)
        samples = []
        
        # Template-based spintax variations for different message types
        template_variations = [
            "{Hello|Hi|Hey|Good day} {first_name}! I {noticed|saw|came across|found} your {profile|work|page|content} and {thought|figured|believe} you might be {interested|curious} in {virtual assistant services|VA support|professional assistance|business solutions}. {Worth a quick chat?|Let's connect!|Interested in learning more?|Would love to discuss this!}",
            
            "{Hey|Hi there|Hello} {first_name}! {Looking to connect with|Reaching out to|Connecting with} {business owners|entrepreneurs|professionals} in {city|your area|the region}. I {provide|offer|specialize in} {VA services|virtual assistance|administrative support} that could {help streamline your operations|save you valuable time|boost your productivity}. {Interested?|Let's chat!|Worth discussing?}",
            
            "{Good {morning|afternoon|day}} {first_name}! I {help|assist|support} {businesses|entrepreneurs|professionals} with {daily operations|administrative tasks|time-consuming work}. {Based on your profile|From what I see|Looking at your work}, this could be {perfect for you|exactly what you need|very beneficial}. {Let me know if you'd like to hear more|Worth a conversation?|Interested in connecting?}",
            
            "{Hi|Hello|Hey there} {first_name}! {Fellow entrepreneur here!|Local business supporter here!|Professional in your network!} I {specialize in|focus on|excel at} {helping businesses grow|streamlining operations|providing administrative support} through {comprehensive VA services|professional virtual assistance|tailored business solutions}. {Could this be helpful?|Let's explore how I can help|Worth a brief discussion?}",
            
            "{Hello|Hi|Greetings} {first_name}! I {noticed you're in|see you're based in|connect with professionals in} {city}. My {VA services|virtual assistance|business support} help {local entrepreneurs|area businesses|regional companies} {save time|increase efficiency|focus on growth}. {Interested in learning more?|Worth connecting about this?|Let's chat about opportunities!}",
            
            "{Hey|Hi|Hello} {first_name}! {Quick question|Reaching out because|Connecting with you since} - are you {looking for ways to|interested in|needing help with} {saving time|streamlining operations|reducing administrative burden}? I {provide|offer|deliver} {professional VA services|comprehensive virtual assistance|business support solutions} that could {make a real difference|be exactly what you need|transform your productivity}. {Let's talk!|Interested?|Worth exploring?}"
        ]
        
        for i in range(min(count, len(template_variations))):
            try:
                # Use one of the template variations
                template_spintax = template_variations[i % len(template_variations)]
                
                # Parse the spintax to generate a sample variation
                sample_variation = SpintaxParser.parse(template_spintax)
                samples.append(sample_variation)
                
                logger.info(f"✅ Generated template-based spintax sample {i+1}")
                    
            except Exception as e:
                logger.error(f"Error generating template spintax sample {i+1}: {e}")
                break
        
        # If we still need more samples, generate additional ones with slight modifications
        while len(samples) < count and len(samples) < 10:  # Max 10 samples
            try:
                # Pick a random template and parse it
                import random
                random_template = random.choice(template_variations)
                sample_variation = SpintaxParser.parse(random_template)
                
                # Avoid exact duplicates
                if sample_variation not in samples:
                    samples.append(sample_variation)
                    
            except Exception as e:
                logger.error(f"Error generating additional spintax sample: {e}")
                break
        
        # If we still don't have enough samples, create more based on the original prompt
        if len(samples) < count:
            logger.info("AI generation failed, using advanced spintax fallback based on original prompt")
            samples = []
            
            # Analyze the original prompt to extract key concepts
            prompt_lower = prompt.lower()
            
            # Create comprehensive spintax based on the original prompt
            def create_advanced_spintax_from_prompt(prompt_text, variation_num):
                # Base structure with extensive variations
                base_template = prompt_text
                
                # Add comprehensive spintax variations to common words and phrases
                spintax_replacements = {
                    # Greetings - extensive variations
                    r'\b(hello|hi|hey|greetings?)\b': '{Hello|Hi|Hey|Greetings|Good morning|Good afternoon|What\'s up|Hey there}',
                    
                    # Action verbs - comprehensive variations
                    r'\b(noticed|saw|found|came across|discovered|spotted)\b': '{noticed|saw|found|came across|discovered|spotted|observed|identified|encountered}',
                    r'\b(help|assist|support|work with)\b': '{help|assist|support|work with|collaborate with|partner with|aid}',
                    r'\b(offer|provide|deliver|give)\b': '{offer|provide|deliver|give|supply|present|bring}',
                    r'\b(specialize|focus|excel|concentrate)\b': '{specialize|focus|excel|concentrate|expertise lies|skilled}',
                    
                    # Business terms - extensive variations
                    r'\b(business|company|venture|enterprise)\b': '{business|company|venture|enterprise|organization|firm|operation}',
                    r'\b(services|solutions|support|assistance|help)\b': '{services|solutions|support|assistance|help|expertise|capabilities|offerings}',
                    r'\b(virtual assistant|VA|assistant)\b': '{virtual assistant|VA|remote assistant|digital assistant|administrative support|business support}',
                    
                    # Descriptive words - comprehensive variations
                    r'\b(professional|skilled|experienced|expert)\b': '{professional|skilled|experienced|expert|qualified|competent|proficient}',
                    r'\b(efficient|effective|productive|streamlined)\b': '{efficient|effective|productive|streamlined|optimized|smooth|systematic}',
                    r'\b(quality|excellent|outstanding|exceptional)\b': '{quality|excellent|outstanding|exceptional|superior|top-notch|premium}',
                    r'\b(reliable|dependable|trustworthy|consistent)\b': '{reliable|dependable|trustworthy|consistent|steadfast|solid|proven}',
                    
                    # Tasks and work - extensive variations
                    r'\b(tasks|work|projects|duties|responsibilities)\b': '{tasks|work|projects|duties|responsibilities|assignments|operations|activities}',
                    r'\b(manage|handle|oversee|coordinate)\b': '{manage|handle|oversee|coordinate|supervise|organize|streamline}',
                    r'\b(administrative|admin|clerical|office)\b': '{administrative|admin|clerical|office|operational|business|organizational}',
                    
                    # Time and efficiency - comprehensive variations
                    r'\b(time|schedule|deadline|timeline)\b': '{time|schedule|deadline|timeline|timeframe|planning|organization}',
                    r'\b(save|reduce|minimize|optimize)\b': '{save|reduce|minimize|optimize|streamline|improve|enhance}',
                    r'\b(busy|overwhelmed|swamped|loaded)\b': '{busy|overwhelmed|swamped|loaded|stretched|packed|hectic}',
                    
                    # Communication and connection - extensive variations
                    r'\b(chat|talk|discuss|connect|communicate)\b': '{chat|talk|discuss|connect|communicate|speak|converse|reach out}',
                    r'\b(interested|curious|keen|eager)\b': '{interested|curious|keen|eager|intrigued|attracted|drawn to}',
                    r'\b(worth|deserve|merit|valuable)\b': '{worth|deserve|merit|valuable|worthwhile|beneficial|advantageous}',
                    
                    # Call to actions - extensive variations
                    r'\b(let me know|reach out|get in touch|contact me)\b': '{let me know|reach out|get in touch|contact me|drop me a line|feel free to message|don\'t hesitate to ask}',
                    r'\b(worth a chat|let\'s connect|interested to discuss)\b': '{worth a chat|let\'s connect|interested to discuss|happy to talk|worth exploring|let\'s talk}',
                    
                    # Industry specific - comprehensive variations
                    r'\b(marketing|sales|promotion|advertising)\b': '{marketing|sales|promotion|advertising|outreach|campaigns|brand building}',
                    r'\b(content|social media|digital|online)\b': '{content|social media|digital|online|web-based|internet|digital marketing}',
                    r'\b(customer|client|lead|prospect)\b': '{customer|client|lead|prospect|contact|potential client|target audience}',
                    
                    # Results and benefits - extensive variations
                    r'\b(grow|increase|boost|improve|enhance)\b': '{grow|increase|boost|improve|enhance|elevate|advance|expand}',
                    r'\b(results|outcomes|success|achievements)\b': '{results|outcomes|success|achievements|progress|accomplishments|gains}',
                    r'\b(profit|revenue|income|earnings)\b': '{profit|revenue|income|earnings|returns|financial gains|bottom line}',
                }
                
                # Apply spintax replacements using regex
                import re
                enhanced_template = base_template
                
                for pattern, replacement in spintax_replacements.items():
                    enhanced_template = re.sub(pattern, replacement, enhanced_template, flags=re.IGNORECASE)
                
                # Add variation-specific customizations
                if variation_num == 1:
                    # More professional tone
                    enhanced_template = enhanced_template.replace('{Hello|Hi|Hey|Greetings|Good morning|Good afternoon|What\'s up|Hey there}', 
                                                                '{Good morning|Good afternoon|Hello|Greetings|Hi there}')
                elif variation_num == 2:
                    # More casual tone
                    enhanced_template = enhanced_template.replace('{Hello|Hi|Hey|Greetings|Good morning|Good afternoon|What\'s up|Hey there}', 
                                                                '{Hey|Hi|What\'s up|Hey there|Hello}')
                elif variation_num == 3:
                    # Balanced approach
                    enhanced_template = enhanced_template.replace('{Hello|Hi|Hey|Greetings|Good morning|Good afternoon|What\'s up|Hey there}', 
                                                                '{Hi|Hello|Hey|Greetings}')
                
                return enhanced_template
            
            # Generate 3 comprehensive spintax variations based on the original prompt
            for i in range(min(count, 3)):
                enhanced_spintax_template = create_advanced_spintax_from_prompt(prompt, i + 1)
                
                # Parse the enhanced template to create a sample variation
                sample_variation = SpintaxParser.parse(enhanced_spintax_template)
                samples.append(sample_variation)
                
            logger.info(f"✅ Generated {len(samples)} comprehensive spintax samples based on original prompt")
        
        return {
            "success": True,
            "samples": samples,
            "original_prompt": prompt,
            "ai_used": False,  # AI is removed
            "message": "Template-based spintax samples (OpenAI functionality removed)"
        }
        
    except Exception as e:
        logger.error(f"Error generating AI spintax samples: {e}")
        return {
            "success": False,
            "error": str(e),
            "samples": []
        }

@app.post("/api/dm-automation/start")
async def start_dm_automation(
    background_tasks: BackgroundTasks,
    account_ids: str = Form(...),
    target_file: Optional[UploadFile] = File(None),
    dm_prompt_file: Optional[UploadFile] = File(None),
    custom_prompt: str = Form(""),
    dms_per_account: int = Form(30),
    current_user: dict = Depends(verify_token_dependency)
):
    """Start Instagram DM Automation script"""
    script_id = generate_script_id()
    
    try:
        # Validate that target file is provided
        if not target_file:
            raise HTTPException(status_code=400, detail={"error": "Target file is required for DM automation. Please upload an Excel/CSV file containing target users with columns like: username, first_name, city, bio"})
        
        # Validate target file format
        if not target_file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail={"error": "Target file must be Excel (.xlsx, .xls) or CSV (.csv) format"})
        # Parse account IDs
        try:
            account_ids_list = json.loads(account_ids)
            if not isinstance(account_ids_list, list) or len(account_ids_list) == 0:
                raise HTTPException(status_code=400, detail={"error": "Invalid account IDs format"})
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail={"error": "Invalid account IDs format"})
        
        # Get selected accounts from the accounts manager
        selected_accounts = instagram_accounts_manager.get_accounts_by_ids(account_ids_list)
        if len(selected_accounts) == 0:
            raise HTTPException(status_code=400, detail={"error": "No valid accounts found"})
        
        # Create temporary accounts file with selected accounts
        accounts_data = []
        for account in selected_accounts:
            accounts_data.append({
                'Username': account['username'],
                'Password': account['password']
            })
        
        # Save accounts to temporary CSV file
        accounts_df = pd.DataFrame(accounts_data)
        accounts_path = f"temp_dm_accounts_{script_id}.csv"
        accounts_df.to_csv(accounts_path, index=False)
        
        # Track the temporary accounts file
        if script_id not in script_temp_files:
            script_temp_files[script_id] = []
        script_temp_files[script_id].append(accounts_path)
        
        target_path = None
        if target_file:
            target_path = save_temp_file(target_file, script_id, "targets")
        
        prompt_path = None
        if dm_prompt_file:
            prompt_path = save_temp_file(dm_prompt_file, script_id, "prompt")
        
        # Initialize script tracking
        active_scripts[script_id] = {
            "type": "dm_automation",
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "user_id": current_user.get('user_id', 'system'),
            "config": {
                "accounts_file": accounts_path,
                "target_file": target_path,
                "prompt_file": prompt_path,
                "custom_prompt": custom_prompt,
                "dms_per_account": dms_per_account,
                "selected_account_ids": account_ids_list
            }
        }
        
        # Initialize stop flag
        script_stop_flags[script_id] = False
        
        log_script_message(script_id, f"DM Automation script started with {len(selected_accounts)} accounts")
        log_script_message(script_id, f"Target: {dms_per_account} DMs per account")
        
        # Start the script in background
        background_tasks.add_task(run_dm_automation_script, script_id)
        
        return {
            "script_id": script_id,
            "status": "started",
            "message": "DM automation script initiated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting DM automation script: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

async def run_dm_automation_script(script_id: str):
    """Run the actual DM automation script"""
    try:
        config = active_scripts[script_id]["config"]
        
        # Initialize stop flag
        script_stop_flags[script_id] = False
        
        # Create log callback function
        def log_callback(message, level="INFO"):
            log_script_message(script_id, message, level)
        
        # Create stop callback function  
        def stop_callback():
            return script_stop_flags.get(script_id, False)
        
        log_script_message(script_id, "Starting Instagram DM automation...")
        
        # Run the automation function
        success = await run_dm_automation(
            script_id=script_id,
            accounts_file=config['accounts_file'],
            target_file=config.get('target_file'),
            prompt_file=config.get('prompt_file'),
            custom_prompt=config.get('custom_prompt', ''),
            dms_per_account=config.get('dms_per_account', 30),
            log_callback=log_callback,
            stop_callback=stop_callback
        )
        
        if success:
            active_scripts[script_id]["status"] = "completed"
            active_scripts[script_id]["end_time"] = datetime.now().isoformat()
            log_script_message(script_id, "DM automation completed successfully!", "SUCCESS")
        else:
            active_scripts[script_id]["status"] = "error"
            active_scripts[script_id]["end_time"] = datetime.now().isoformat()
            active_scripts[script_id]["error"] = "Script execution failed"
            log_script_message(script_id, "DM automation script failed", "ERROR")
        
    except Exception as e:
        active_scripts[script_id]["status"] = "error"
        active_scripts[script_id]["end_time"] = datetime.now().isoformat()
        active_scripts[script_id]["error"] = str(e)
        log_script_message(script_id, f"Script error: {e}", "ERROR")
        traceback.print_exc()
    finally:
        # Clean up temporary files
        cleanup_temp_files(script_id)

# Warmup Endpoints
@app.post("/api/warmup/start")
async def start_warmup(
    background_tasks: BackgroundTasks,
    account_ids: str = Form(...),
    warmup_duration_min: int = Form(10),
    warmup_duration_max: int = Form(400),
    scheduler_delay: int = Form(0),
    feed_scroll: bool = Form(True),
    watch_reels: bool = Form(True),
    like_reels: bool = Form(True),
    like_posts: bool = Form(True),
    explore_page: bool = Form(True),
    random_visits: bool = Form(True),
    activity_delay_min: int = Form(3),
    activity_delay_max: int = Form(7),
    scroll_attempts_min: int = Form(5),
    scroll_attempts_max: int = Form(10),
    current_user: dict = Depends(verify_token_dependency)
):
    """Start Instagram Account Warmup script"""
    script_id = generate_script_id()
    
    try:
        # Parse account IDs
        try:
            account_ids_list = json.loads(account_ids)
            if not isinstance(account_ids_list, list) or len(account_ids_list) == 0:
                raise HTTPException(status_code=400, detail={"error": "Invalid account IDs format"})
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail={"error": "Invalid account IDs format"})
        
        # Get selected accounts from the accounts manager
        selected_accounts = instagram_accounts_manager.get_accounts_by_ids(account_ids_list)
        if len(selected_accounts) == 0:
            raise HTTPException(status_code=400, detail={"error": "No valid accounts found"})
        
        # Create temporary accounts file with selected accounts
        accounts_data = []
        for account in selected_accounts:
            accounts_data.append({
                'Username': account['username'],
                'Password': account['password']
            })
        
        # Save accounts to temporary CSV file
        accounts_df = pd.DataFrame(accounts_data)
        accounts_path = f"temp_warmup_accounts_{script_id}.csv"
        accounts_df.to_csv(accounts_path, index=False)
        
        # Track the temporary accounts file
        if script_id not in script_temp_files:
            script_temp_files[script_id] = []
        script_temp_files[script_id].append(accounts_path)
        
        # Initialize script tracking
        active_scripts[script_id] = {
            "type": "warmup",
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "user_id": current_user.get('user_id', 'system'),
            "config": {
                "accounts_file": accounts_path,
                "warmup_duration_min": warmup_duration_min,
                "warmup_duration_max": warmup_duration_max,
                "scheduler_delay": scheduler_delay,
                "selected_account_ids": account_ids_list,
                "activities": {
                    "feed_scroll": feed_scroll,
                    "watch_reels": watch_reels,
                    "like_reels": like_reels,
                    "like_posts": like_posts,
                    "explore_page": explore_page,
                    "random_visits": random_visits
                },
                "timing": {
                    "activity_delay": (activity_delay_min, activity_delay_max),
                    "scroll_attempts": (scroll_attempts_min, scroll_attempts_max)
                }
            }
        }
        
        # Initialize stop flag
        script_stop_flags[script_id] = False
        
        log_script_message(script_id, f"Account warmup script started")
        log_script_message(script_id, f"Random duration range: {warmup_duration_min}-{warmup_duration_max} minutes per session")
        if scheduler_delay > 0:
            log_script_message(script_id, f"🔄 RECURRING MODE: {scheduler_delay} hour delay between sessions")
        else:
            log_script_message(script_id, f"🎯 SINGLE MODE: One-time execution")
        log_script_message(script_id, f"Dynamic account processing: All selected accounts will be used")
        
        # Start the script in background
        background_tasks.add_task(run_warmup_script, script_id)
        
        return {
            "script_id": script_id,
            "status": "started",
            "message": "Account warmup script initiated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting warmup script: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

async def run_warmup_script(script_id: str):
    """Run the actual warmup script with recurring functionality"""
    try:
        config = active_scripts[script_id]["config"]
        
        # Create log callback function
        def log_callback(message, level="INFO"):
            log_script_message(script_id, message, level)
        
        # Create stop callback function
        def stop_callback():
            return script_stop_flags.get(script_id, False)
        
        # Get configuration
        scheduler_delay_hours = config.get('scheduler_delay', 0)
        duration_min = config.get('warmup_duration_min', 10)
        duration_max = config.get('warmup_duration_max', 400)
        
        # Determine if this is recurring or single run
        is_recurring = scheduler_delay_hours > 0
        session_count = 0
        
        log_script_message(script_id, f"Starting warmup automation...")
        log_script_message(script_id, f"Duration range: {duration_min}-{duration_max} minutes per session")
        
        if is_recurring:
            log_script_message(script_id, f"🔄 RECURRING MODE: Will run sessions with {scheduler_delay_hours} hour delay between them")
            log_script_message(script_id, f"⏹️ Stop the script manually to end recurring sessions")
        else:
            log_script_message(script_id, f"🎯 SINGLE MODE: Will run one session and complete")
        
        # Main execution loop
        while True:
            if stop_callback():
                log_script_message(script_id, "Script stopped by user", "INFO")
                active_scripts[script_id]["status"] = "stopped"
                active_scripts[script_id]["end_time"] = datetime.now().isoformat()
                return
            
            session_count += 1
            session_start_time = datetime.now()
            
            # Generate random duration for this session
            import random
            random_duration = random.randint(duration_min, duration_max)
            
            log_script_message(script_id, f"")
            log_script_message(script_id, f"🚀 Starting Session #{session_count}")
            log_script_message(script_id, f"📊 Session duration: {random_duration} minutes")
            log_script_message(script_id, f"⏰ Session started at: {session_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Run the automation function for this session
            success = await run_warmup_automation(
                script_id=script_id,
                accounts_file=config['accounts_file'],
                warmup_duration=random_duration,
                activities=config['activities'],
                timing=config['timing'],
                log_callback=log_callback,
                stop_callback=stop_callback
            )
            
            session_end_time = datetime.now()
            session_duration = (session_end_time - session_start_time).total_seconds() / 60
            
            if success:
                log_script_message(script_id, f"✅ Session #{session_count} completed successfully!", "SUCCESS")
                log_script_message(script_id, f"📈 Actual session duration: {session_duration:.1f} minutes")
            else:
                log_script_message(script_id, f"❌ Session #{session_count} failed", "ERROR")
                if not is_recurring:
                    active_scripts[script_id]["status"] = "error"
                    active_scripts[script_id]["end_time"] = datetime.now().isoformat()
                    active_scripts[script_id]["error"] = "Session execution failed"
                    return
                else:
                    log_script_message(script_id, f"🔄 Continuing to next session despite failure...", "WARNING")
            
            # Check if this is a single run (no recurring)
            if not is_recurring:
                active_scripts[script_id]["status"] = "completed"
                active_scripts[script_id]["end_time"] = datetime.now().isoformat()
                log_script_message(script_id, "🎯 Single session warmup completed successfully!", "SUCCESS")
                return
            
            # For recurring mode, wait for the specified delay
            if scheduler_delay_hours > 0:
                delay_seconds = scheduler_delay_hours * 3600
                next_session_time = datetime.now() + timedelta(hours=scheduler_delay_hours)
                
                log_script_message(script_id, f"")
                log_script_message(script_id, f"⏳ Waiting {scheduler_delay_hours} hour{'s' if scheduler_delay_hours > 1 else ''} before next session...")
                log_script_message(script_id, f"🕐 Next session scheduled for: {next_session_time.strftime('%Y-%m-%d %H:%M:%S')}")
                log_script_message(script_id, f"⏹️ You can stop the script anytime during this wait")
                
                # Wait with periodic checks for stop signal (check every minute)
                start_wait_time = time_module.time()
                while time_module.time() - start_wait_time < delay_seconds:
                    if stop_callback():
                        log_script_message(script_id, "Script stopped during delay period", "INFO")
                        active_scripts[script_id]["status"] = "stopped"
                        active_scripts[script_id]["end_time"] = datetime.now().isoformat()
                        return
                    
                    # Log progress every 15 minutes during long waits
                    elapsed_wait = time_module.time() - start_wait_time
                    remaining_wait = delay_seconds - elapsed_wait
                    if elapsed_wait > 0 and int(elapsed_wait) % 900 == 0:  # Every 15 minutes
                        remaining_hours = remaining_wait / 3600
                        log_script_message(script_id, f"⏳ Still waiting... {remaining_hours:.1f} hours remaining until next session")
                    
                    await asyncio.sleep(60)  # Check every minute
                
                log_script_message(script_id, f"✅ Delay period completed. Preparing for next session...")
        
    except Exception as e:
        active_scripts[script_id]["status"] = "error"
        active_scripts[script_id]["end_time"] = datetime.now().isoformat()
        active_scripts[script_id]["error"] = str(e)
        log_script_message(script_id, f"Script error: {e}", "ERROR")
        traceback.print_exc()
    finally:
        # Clean up temporary files
        cleanup_temp_files(script_id)

# Script Management Endpoints
@app.get("/api/script/{script_id}/status")
async def get_script_status(script_id: str, current_user: dict = Depends(verify_token_dependency)):
    """Get status of a running script"""
    if script_id not in active_scripts:
        raise HTTPException(status_code=404, detail={"error": "Script not found"})
    
    script_data = active_scripts[script_id].copy()
    
    # Add auto_stop flag for completed, error, or stopped scripts
    auto_stop = script_data.get("status") in ["completed", "error", "stopped"]
    script_data["auto_stop"] = auto_stop
    
    return script_data

@app.get("/api/script/{script_id}/logs")
async def get_script_logs(script_id: str, current_user: dict = Depends(verify_token_dependency)):
    """Get logs for a specific script"""
    logs = script_logs.get(script_id, [])
    return {"logs": logs}

@app.post("/api/script/{script_id}/stop")
async def stop_script(
    script_id: str, 
    stop_request: StopScriptRequest,
    current_user: dict = Depends(verify_token_dependency)
):
    """Stop a running script"""
    if script_id not in active_scripts:
        raise HTTPException(status_code=404, detail={"error": "Script not found"})
    
    if active_scripts[script_id]["status"] == "running":
        # Set stop flag for the script
        script_stop_flags[script_id] = True
        active_scripts[script_id]["status"] = "stopped"
        active_scripts[script_id]["end_time"] = datetime.now().isoformat()
        active_scripts[script_id]["stop_reason"] = stop_request.reason
        
        # Log the stop reason
        log_script_message(script_id, stop_request.reason, "WARNING")
        
        # Clean up temporary files when script is stopped
        cleanup_temp_files(script_id)
        return {
            "status": "stopped", 
            "message": "Script stopped successfully", 
            "reason": stop_request.reason
        }
    
    return {
        "status": active_scripts[script_id]["status"], 
        "message": "Script not running"
    }

@app.get("/api/scripts")
async def list_scripts(current_user: dict = Depends(verify_token_dependency)):
    """List all scripts with their status - filtered by user or all for admin"""
    user_id = current_user.get('user_id', 'system')
    user_role = current_user.get('role', 'va')
    
    # Admin can see all scripts, VAs only see their own
    if user_role == 'admin':
        filtered_scripts = active_scripts
    else:
        filtered_scripts = {
            script_id: script_data 
            for script_id, script_data in active_scripts.items() 
            if script_data.get('user_id') == user_id
        }
    
    return filtered_scripts

@app.get("/api/scripts/running")
async def list_running_scripts(current_user: dict = Depends(verify_token_dependency)):
    """List only running scripts - filtered by user or all for admin"""
    user_id = current_user.get('user_id', 'system')
    user_role = current_user.get('role', 'va')
    
    # Filter running scripts first
    running_scripts = {
        script_id: script_data 
        for script_id, script_data in active_scripts.items() 
        if script_data.get('status') == 'running'
    }
    
    # Admin can see all running scripts, VAs only see their own
    if user_role == 'admin':
        filtered_scripts = running_scripts
    else:
        filtered_scripts = {
            script_id: script_data 
            for script_id, script_data in running_scripts.items() 
            if script_data.get('user_id') == user_id
        }
    
    # Convert to array format for frontend compatibility
    script_array = []
    for script_id, script_data in filtered_scripts.items():
        script_item = script_data.copy()
        script_item['script_id'] = script_id
        script_array.append(script_item)
    
    return script_array

@app.get("/api/scripts/stats")
async def get_script_stats(current_user: dict = Depends(verify_token_dependency)):
    """Get script statistics for the current user or all users for admin"""
    user_id = current_user.get('user_id', 'system')
    user_role = current_user.get('role', 'va')
    
    # Admin can see all scripts, VAs only see their own
    if user_role == 'admin':
        user_scripts = active_scripts
    else:
        user_scripts = {
            script_id: script_data 
            for script_id, script_data in active_scripts.items() 
            if script_data.get('user_id') == user_id
        }
    
    # Calculate statistics
    total_scripts = len(user_scripts)
    running_scripts = len([s for s in user_scripts.values() if s['status'] == 'running'])
    completed_scripts = len([s for s in user_scripts.values() if s['status'] == 'completed'])
    error_scripts = len([s for s in user_scripts.values() if s['status'] == 'error'])
    stopped_scripts = len([s for s in user_scripts.values() if s['status'] == 'stopped'])
    
    # Calculate per-script-type statistics
    script_types = {}
    for script_data in user_scripts.values():
        script_type = script_data.get('type', 'unknown')
        if script_type not in script_types:
            script_types[script_type] = {
                'total': 0,
                'running': 0,
                'completed': 0,
                'error': 0,
                'stopped': 0
            }
        
        script_types[script_type]['total'] += 1
        script_types[script_type][script_data['status']] += 1
    
    return {
        'user_id': user_id,
        'user_role': user_role,
        'total_scripts': total_scripts,
        'running_scripts': running_scripts,
        'completed_scripts': completed_scripts,
        'error_scripts': error_scripts,
        'stopped_scripts': stopped_scripts,
        'script_types': script_types,
        'recent_scripts': sorted(
            user_scripts.values(),
            key=lambda x: x['start_time'],
            reverse=True
        )[:10]  # Last 10 scripts
    }

@app.get("/api/script/{script_id}/download-logs")
async def download_script_logs(script_id: str):
    """Download logs for a specific script as a text file"""
    if script_id not in script_logs:
        raise HTTPException(status_code=404, detail={"error": "Script logs not found"})
    
    logs = script_logs.get(script_id, [])
    log_content = "\n".join(logs)
    
    # Create logs file
    log_filename = f"script_{script_id}_logs.txt"
    log_path = os.path.join(LOGS_FOLDER, log_filename)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(log_content)
    
    return FileResponse(log_path, filename=log_filename, media_type='text/plain')

@app.post("/api/script/{script_id}/clear-logs")
async def clear_script_logs(script_id: str):
    """Clear logs for a specific script"""
    if script_id not in script_logs:
        raise HTTPException(status_code=404, detail={"error": "Script logs not found"})
    
    script_logs[script_id] = []
    return {"message": "Logs cleared successfully"}

@app.get("/api/script/{script_id}/responses")
async def get_dm_responses(script_id: str, current_user: dict = Depends(verify_token_dependency)):
    """Get positive responses for a completed DM automation script"""
    try:
        # Check if responses file exists
        responses_file = os.path.join(LOGS_FOLDER, f'dm_responses_{script_id}.json')
        
        if not os.path.exists(responses_file):
            return {
                "responses": [],
                "message": f"No responses found for this script. Looking for: {responses_file}"
            }
        
        # Read and return responses
        with open(responses_file, 'r', encoding='utf-8') as f:
            responses = json.load(f)
        
        # Group responses by account for better organization
        grouped_responses = {}
        for response in responses:
            account = response['account']
            if account not in grouped_responses:
                grouped_responses[account] = []
            grouped_responses[account].append({
                'responder': response['responder'],
                'message': response['message'],
                'timestamp': response['timestamp']
            })
        
        return {
            "responses": responses,
            "grouped_responses": grouped_responses,
            "total_responses": len(responses),
            "accounts_with_responses": len(grouped_responses)
        }
        
    except Exception as e:
        logger.error(f"Error fetching responses for script {script_id}: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

# Admin Endpoints
@app.get("/api/admin/users")
async def get_all_users(current_user: dict = Depends(admin_required_dependency)):
    """Get all users (admin only)"""
    try:
        users = user_manager.get_all_users()
        # Map user_id to id for frontend compatibility
        for user in users:
            # Handle both 'user_id' and 'id' fields for backward compatibility
            user_id = user.get('user_id') or user.get('id')
            if user_id:
                user['id'] = user_id
                user['user_id'] = user_id  # Ensure both fields exist
        return {'success': True, 'users': users}
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.post("/api/admin/users")
async def create_user(user_data: UserCreate, current_user: dict = Depends(admin_required_dependency)):
    """Create new user (admin only)"""
    try:
        if user_data.role not in ['admin', 'va']:
            raise HTTPException(status_code=400, detail={'success': False, 'message': 'Invalid role'})
        
        result = user_manager.create_user(user_data.name, user_data.username, user_data.password, user_data.role)
        
        if result['success']:
            log_user_activity('user_created', f"Created user {user_data.username} with role {user_data.role}", current_user['user_id'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create user error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.put("/api/admin/users/{user_id}")
async def update_user(
    user_id: str, 
    user_update: UserUpdate, 
    current_user: dict = Depends(admin_required_dependency)
):
    """Update user (admin only)"""
    try:
        updates = {}
        
        # Allow updating name, password, is_active
        if user_update.name is not None:
            updates['name'] = user_update.name
        if user_update.password is not None:
            updates['password'] = user_update.password
        if user_update.is_active is not None:
            updates['is_active'] = user_update.is_active
        
        if not updates:
            raise HTTPException(status_code=400, detail={'success': False, 'message': 'No updates provided'})
        
        result = user_manager.update_user(user_id, updates)
        
        if result['success']:
            log_user_activity('user_updated', f"Updated user {user_id}", current_user['user_id'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.post("/api/admin/users/{user_id}/deactivate")
async def deactivate_user(user_id: str, current_user: dict = Depends(admin_required_dependency)):
    """Deactivate user (admin only)"""
    try:
        result = user_manager.deactivate_user(user_id)
        
        if result['success']:
            log_user_activity('user_deactivated', f"Deactivated user {user_id}", current_user['user_id'])
        
        return result
        
    except Exception as e:
        logger.error(f"Deactivate user error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(admin_required_dependency)):
    """Delete user permanently (admin only)"""
    try:
        result = user_manager.delete_user(user_id)
        
        if result['success']:
            log_user_activity('user_deleted', f"Deleted user {user_id}", current_user['user_id'])
        
        return result
        
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.get("/api/admin/activity-logs")
async def get_activity_logs(current_user: dict = Depends(admin_required_dependency)):
    """Get activity logs (admin only)"""
    try:
        logs = user_manager.get_activity_logs()
        return {'success': True, 'logs': logs}
    except Exception as e:
        logger.error(f"Get activity logs error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.get("/api/admin/stats")
async def get_admin_stats(current_user: dict = Depends(admin_required_dependency)):
    """Get admin dashboard statistics"""
    try:
        users = user_manager.get_all_users()
        logs = user_manager.get_activity_logs(50)
        
        stats = {
            'total_users': len(users),
            'active_users': len([u for u in users if u.get('is_active', True)]),
            'admin_users': len([u for u in users if u['role'] == 'admin']),
            'va_users': len([u for u in users if u['role'] == 'va']),
            'total_scripts': len(active_scripts),
            'running_scripts': len([s for s in active_scripts.values() if s['status'] == 'running']),
            'recent_activity': logs[:10]
        }
        
        return {'success': True, 'stats': stats}
    except Exception as e:
        logger.error(f"Get admin stats error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.get("/api/admin/script-logs")
async def get_admin_script_logs(
    user_id: str = Query(None, description="Filter by user ID"),
    limit: int = Query(100, description="Maximum number of logs to return"),
    current_user: dict = Depends(admin_required_dependency)
):
    """Get script execution logs for admin dashboard"""
    try:
        all_scripts = []
        
        # Get all active/running scripts
        if active_scripts:
            for script_id, script_data in active_scripts.items():
                try:
                    # Get user details
                    user_data = user_manager.get_user_by_id(script_data.get('user_id', 'system'))
                    user_name = user_data.get('name', 'System') if user_data else 'System'
                    user_username = user_data.get('username', 'system') if user_data else 'system'
                    
                    script_log = {
                        'script_id': script_id,
                        'user_id': script_data.get('user_id', 'system'),
                        'user_name': user_name,
                        'user_username': user_username,
                        'script_type': script_data.get('type', 'unknown'),
                        'status': script_data.get('status', 'unknown'),
                        'start_time': script_data.get('start_time', ''),
                        'end_time': script_data.get('end_time'),
                        'error': script_data.get('error'),
                        'stop_reason': script_data.get('stop_reason'),
                        'config': script_data.get('config', {}),
                        'logs_available': script_id in script_logs and len(script_logs[script_id]) > 0
                    }
                    
                    # Filter by user_id if specified
                    if not user_id or script_data.get('user_id') == user_id:
                        all_scripts.append(script_log)
                except Exception as script_error:
                    logger.error(f"Error processing script {script_id}: {script_error}")
                    continue
        
        # Sort by start_time (most recent first)
        all_scripts.sort(key=lambda x: x.get('start_time', ''), reverse=True)
        
        # Apply limit
        limited_scripts = all_scripts[:limit]
        
        return {'success': True, 'script_logs': limited_scripts}
    except Exception as e:
        logger.error(f"Get admin script logs error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

# Instagram Accounts Management Endpoints
@app.get("/api/instagram-accounts")
async def get_instagram_accounts(current_user: dict = Depends(verify_token_dependency)):
    """Get all Instagram accounts with proxy information"""
    try:
        accounts = instagram_accounts_manager.get_all_accounts()
        
        # Enrich each account with proxy information
        for account in accounts:
            username = account.get('username')
            if username:
                # Get proxy assignment
                proxy_string = proxy_manager.get_account_proxy(username)
                if proxy_string:
                    proxy_info = proxy_manager.parse_proxy(proxy_string)
                    proxy_index = proxy_manager.get_all_proxies().index(proxy_string) if proxy_string in proxy_manager.get_all_proxies() else -1
                    
                    account['proxy'] = {
                        'assigned': True,
                        'proxy_string': proxy_string,
                        'proxy_index': proxy_index + 1 if proxy_index >= 0 else None,
                        'host': proxy_info['host'] if proxy_info else None,
                        'port': proxy_info['port'] if proxy_info else None,
                        'username': proxy_info['username'] if proxy_info else None
                    }
                    # Add fields that frontend expects
                    account['has_proxy'] = True
                    account['proxy_index'] = proxy_index + 1 if proxy_index >= 0 else None
                    account['proxy_host'] = proxy_info['host'] if proxy_info else None
                    account['proxy_port'] = proxy_info['port'] if proxy_info else None
                else:
                    account['proxy'] = {
                        'assigned': False,
                        'proxy_string': None,
                        'proxy_index': None,
                        'host': None,
                        'port': None,
                        'username': None
                    }
                    # Add fields that frontend expects
                    account['has_proxy'] = False
                    account['proxy_index'] = None
                    account['proxy_host'] = None
                    account['proxy_port'] = None
        
        return {'success': True, 'accounts': accounts}
    except Exception as e:
        logger.error(f"Get Instagram accounts error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.get("/api/instagram-accounts/active")
async def get_active_instagram_accounts(current_user: dict = Depends(verify_token_dependency)):
    """Get only active Instagram accounts with proxy information"""
    try:
        accounts = instagram_accounts_manager.get_active_accounts()
        
        # Enrich each account with proxy information
        for account in accounts:
            username = account.get('username')
            if username:
                # Get proxy assignment
                proxy_string = proxy_manager.get_account_proxy(username)
                if proxy_string:
                    proxy_info = proxy_manager.parse_proxy(proxy_string)
                    proxy_index = proxy_manager.get_all_proxies().index(proxy_string) if proxy_string in proxy_manager.get_all_proxies() else -1
                    
                    account['proxy'] = {
                        'assigned': True,
                        'proxy_string': proxy_string,
                        'proxy_index': proxy_index + 1 if proxy_index >= 0 else None,
                        'host': proxy_info['host'] if proxy_info else None,
                        'port': proxy_info['port'] if proxy_info else None,
                        'username': proxy_info['username'] if proxy_info else None
                    }
                    # Add fields that frontend expects
                    account['has_proxy'] = True
                    account['proxy_index'] = proxy_index + 1 if proxy_index >= 0 else None
                    account['proxy_host'] = proxy_info['host'] if proxy_info else None
                    account['proxy_port'] = proxy_info['port'] if proxy_info else None
                else:
                    account['proxy'] = {
                        'assigned': False,
                        'proxy_string': None,
                        'proxy_index': None,
                        'host': None,
                        'port': None,
                        'username': None
                    }
                    # Add fields that frontend expects
                    account['has_proxy'] = False
                    account['proxy_index'] = None
                    account['proxy_host'] = None
                    account['proxy_port'] = None
        
        return {'success': True, 'accounts': accounts}
    except Exception as e:
        logger.error(f"Get active Instagram accounts error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.post("/api/instagram-accounts")
async def add_instagram_account(
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(""),
    email_Password: str = Form(""),
    notes: str = Form(""),
    totp_secret: str = Form(""),
    current_user: dict = Depends(admin_required_dependency)
):
    """Add a new Instagram account"""
    try:
        new_account = instagram_accounts_manager.add_account(
            username=username,
            password=password,
            email=email,
            email_Password=email_Password,
            notes=notes,
            totp_secret=totp_secret
        )
        log_user_activity(current_user['username'], f"Added Instagram account: {username}")
        return {'success': True, 'account': new_account}
    except ValueError as e:
        raise HTTPException(status_code=400, detail={'success': False, 'message': str(e)})
    except Exception as e:
        logger.error(f"Add Instagram account error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.put("/api/instagram-accounts/{account_id}")
async def update_instagram_account(
    account_id: str,
    username: str = Form(None),
    password: str = Form(None),
    email: str = Form(None),
    email_Password: str = Form(None),
    notes: str = Form(None),
    totp_secret: str = Form(None),
    is_active: bool = Form(None),
    current_user: dict = Depends(admin_required_dependency)
):
    """Update an existing Instagram account"""
    try:
        updates = {}
        if username is not None:
            updates['username'] = username
        if password is not None:
            updates['password'] = password
        if email is not None:
            updates['email'] = email
        if email_Password is not None:
            updates['email_Password'] = email_Password
        if notes is not None:
            updates['notes'] = notes
        if totp_secret is not None:
            updates['totp_secret'] = totp_secret
        if is_active is not None:
            updates['is_active'] = is_active
        
        if not updates:
            raise HTTPException(status_code=400, detail={'success': False, 'message': 'No updates provided'})
        
        success = instagram_accounts_manager.update_account(account_id, updates)
        if success:
            log_user_activity(current_user['username'], f"Updated Instagram account: {account_id}")
            return {'success': True, 'message': 'Account updated successfully'}
        else:
            raise HTTPException(status_code=404, detail={'success': False, 'message': 'Account not found'})
    except ValueError as e:
        raise HTTPException(status_code=400, detail={'success': False, 'message': str(e)})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update Instagram account error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.delete("/api/instagram-accounts/{account_id}")
async def delete_instagram_account(
    account_id: str,
    current_user: dict = Depends(admin_required_dependency)
):
    """Delete an Instagram account"""
    try:
        success = instagram_accounts_manager.delete_account(account_id)
        if success:
            log_user_activity(current_user['username'], f"Deleted Instagram account: {account_id}")
            return {'success': True, 'message': 'Account deleted successfully'}
        else:
            raise HTTPException(status_code=404, detail={'success': False, 'message': 'Account not found'})
    except Exception as e:
        logger.error(f"Delete Instagram account error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.post("/api/instagram-accounts/import")
async def import_instagram_accounts(
    accounts_file: UploadFile = File(...),
    current_user: dict = Depends(admin_required_dependency)
):
    """Import Instagram accounts from Excel/CSV file"""
    try:
        # Check file extension
        if not accounts_file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail={'success': False, 'message': 'Only CSV and Excel files are supported'})
        
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(accounts_file.filename)[1]) as tmp_file:
            content = await accounts_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Import accounts
            result = instagram_accounts_manager.import_accounts_from_file(tmp_file_path)
            
            if result['success']:
                log_user_activity(current_user['username'], f"Imported {result['added_count']} Instagram accounts")
                return {'success': True, 'result': result}
            else:
                raise HTTPException(status_code=400, detail={'success': False, 'message': result['error']})
        
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Import Instagram accounts error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

# Proxy Management Endpoints
@app.get("/api/proxies")
async def get_all_proxies(current_user: dict = Depends(admin_required_dependency)):
    """Get all available proxies and their status"""
    try:
        proxies = proxy_manager.get_all_proxies()
        assignments = proxy_manager.get_all_assignments()
        usage_stats = proxy_manager.get_proxy_usage_stats()
        available_indices = proxy_manager.get_available_proxy_indices()
        
        # Get simple assignments for faster lookup
        simple_assignments = proxy_manager.load_assignments()
        
        proxy_list = []
        for i, proxy in enumerate(proxies):
            proxy_info = proxy_manager.parse_proxy(proxy)
            is_assigned = proxy in simple_assignments.values()
            assigned_to = next(
                (account for account, assigned_proxy in simple_assignments.items() if assigned_proxy == proxy), 
                None
            )
            
            proxy_list.append({
                'index': i + 1,
                'proxy': proxy,
                'host': proxy_info['host'] if proxy_info else None,
                'port': proxy_info['port'] if proxy_info else None,
                'is_assigned': is_assigned,
                'assigned_to': assigned_to
            })
        
        return {
            'success': True,
            'proxies': proxy_list,
            'usage_stats': usage_stats,
            'available_indices': available_indices
        }
    except Exception as e:
        logger.error(f"Get proxies error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.get("/api/proxy-assignments")
async def get_proxy_assignments(current_user: dict = Depends(verify_token_dependency)):
    """Get all proxy assignments"""
    try:
        assignments = proxy_manager.get_all_assignments()
        return {'success': True, 'assignments': assignments}
    except Exception as e:
        logger.error(f"Get proxy assignments error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': 'Internal server error'})

@app.post("/api/proxy-assignments")
async def assign_proxy(
    username: str = Form(...),
    proxy_index: Optional[int] = Form(None),
    current_user: dict = Depends(admin_required_dependency)
):
    """Assign a proxy to an Instagram account"""
    try:
        logger.info(f"Attempting to assign proxy {proxy_index} to account {username}")
        result = instagram_accounts_manager.assign_proxy_to_account(username, proxy_index)
        
        logger.info(f"Proxy assignment result: {result}")
        
        if result['success']:
            log_user_activity(
                'proxy_assign',
                f"Assigned proxy {proxy_index if proxy_index else 'auto'} to account {username}",
                current_user['user_id']
            )
            response = {'success': True, 'message': result['message'], 'proxy': result.get('proxy')}
            logger.info(f"Returning success response: {response}")
            return response
        else:
            error_message = result.get('error', 'Unknown error occurred')
            logger.error(f"Proxy assignment failed: {error_message}")
            raise HTTPException(status_code=400, detail={'success': False, 'message': error_message})
            
    except HTTPException as he:
        logger.error(f"HTTP Exception in proxy assignment: {he.detail}")
        raise
    except ValueError as ve:
        logger.error(f"ValueError in proxy assignment: {str(ve)}")
        raise HTTPException(status_code=400, detail={'success': False, 'message': str(ve)})
    except Exception as e:
        logger.error(f"Unexpected error in proxy assignment: {str(e)}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': f'Internal server error: {str(e)}'})

@app.put("/api/proxy-assignments/{username}")
async def reassign_proxy(
    username: str,
    new_proxy_index: int = Form(...),
    current_user: dict = Depends(admin_required_dependency)
):
    """Reassign a different proxy to an Instagram account"""
    try:
        result = instagram_accounts_manager.reassign_proxy(username, new_proxy_index)
        
        if result['success']:
            log_user_activity(
                'proxy_reassign',
                f"Reassigned proxy {new_proxy_index + 1} to account {username}",
                current_user['user_id']
            )
            return {'success': True, 'message': result['message'], 'proxy': result.get('proxy')}
        else:
            raise HTTPException(status_code=400, detail={'success': False, 'message': result['error']})
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reassign proxy error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': str(e)})

@app.delete("/api/proxy-assignments/{username}")
async def remove_proxy_assignment(
    username: str,
    current_user: dict = Depends(admin_required_dependency)
):
    """Remove proxy assignment from an Instagram account"""
    try:
        # Use proxy_manager instead of instagram_accounts_manager
        proxy_manager.remove_proxy_assignment(username)
        
        log_user_activity(
            'proxy_remove',
            f"Removed proxy assignment from account {username}",
            current_user['user_id']
        )
        return {'success': True, 'message': f'Proxy assignment removed from {username}'}
            
    except ValueError as ve:
        # Account doesn't have a proxy assigned
        logger.warning(f"Remove proxy assignment warning: {ve}")
        raise HTTPException(status_code=404, detail={'success': False, 'message': str(ve)})
    except Exception as e:
        logger.error(f"Remove proxy assignment error: {e}")
        raise HTTPException(status_code=500, detail={'success': False, 'message': str(e)})

# File validation endpoints
@app.post("/api/daily-post/validate")
async def validate_daily_post_files(
    media_file: UploadFile = File(...),
    current_user: dict = Depends(verify_token_dependency)
):
    """Validate uploaded files before starting the script"""
    try:
        errors = []
        
        # Validate media file
        if not media_file:
            errors.append("Media file is required")
        else:
            is_image = allowed_file(media_file.filename, 'images')
            is_video = allowed_file(media_file.filename, 'videos')
            if not (is_image or is_video):
                errors.append("Invalid media file format. Use supported image/video formats")
        
        if errors:
            raise HTTPException(status_code=400, detail={"valid": False, "errors": errors})
        
        return {
            "valid": True, 
            "message": "Files validated successfully",
            "media_type": "video" if is_video else "image"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"valid": False, "errors": [str(e)]})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
