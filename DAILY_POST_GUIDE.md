# Instagram Daily Post Automation - Troubleshooting Guide

## Issues Fixed ✅

### 1. Login Page Timeout Issue
**Problem:** The script was failing with "Login form not found" timeout errors.

**Solution:**
- ✅ Improved browser launch with fallback options
- ✅ Enhanced login form detection with multiple selectors
- ✅ Better error handling and timeout management
- ✅ Removed overly complex enhanced authentication that was causing conflicts

### 2. Browser Launch Failures
**Problem:** Script was failing to launch Chrome browser properly.

**Solution:**
- ✅ Added fallback browser launch methods
- ✅ Improved error handling for browser initialization
- ✅ Simplified browser arguments for better compatibility

### 3. Missing Dependencies
**Problem:** Import errors and missing traceback module.

**Solution:**
- ✅ Added missing `import traceback` statement
- ✅ Fixed import dependencies
- ✅ Removed cached bytecode conflicts

## How the Daily Post Script Works 🔄

### 1. **Initialization Phase**
```
📋 Load account credentials from Excel/CSV file
📁 Validate media file exists and is supported format
🔧 Set up proxy assignments for accounts
📊 Create automation instance with logging
```

### 2. **Browser Setup Phase**
```
🚀 Launch Chromium browser (with Chrome fallback)
🌐 Configure user agent and viewport
🍪 Set up proxy configuration if assigned
📱 Create new browser context and page
```

### 3. **Authentication Phase**
```
🔑 Navigate to Instagram login page
🍪 Handle cookie consent dialogs
⌨️ Enter username and password
🔐 Handle 2FA if TOTP secret is available
💾 Handle "Save login info" dialogs
✅ Verify successful login to home page
```

### 4. **Post Creation Phase**
```
📝 Find and click "Create" button
📋 Select "Post" option if available
📁 Upload media file (image or video)
➡️ Click first "Next" button (crop/edit)
➡️ Click second "Next" button (filters)
📝 Add caption (custom or auto-generated)
🚀 Click "Share" button to publish
⏳ Wait for post completion confirmation
```

### 5. **Cleanup Phase**
```
✅ Log successful completion
🔄 Close browser instance
📊 Return success/failure status
```

## Configuration Requirements 📋

### 1. **Accounts File (Excel/CSV)**
```
| Username          | Password    |
|-------------------|-------------|
| your_username     | your_pass   |
| another_user      | another_pass|
```

### 2. **Media File**
**Supported Formats:**
- **Images:** .jpg, .jpeg, .png, .gif, .bmp, .webp
- **Videos:** .mp4, .mov, .avi, .mkv, .webm, .m4v

### 3. **TOTP Secrets (Optional)**
For automatic 2FA handling, add TOTP secrets to `instagram_accounts.json`:
```json
{
  "your_username": {
    "totp_secret": "YOUR_BASE32_SECRET_HERE"
  }
}
```

### 4. **Proxy Configuration (Optional)**
Proxies are automatically assigned from `proxy_assignments.json`

## Common Issues & Solutions 🔧

### Issue: "Browser launch failed"
**Solutions:**
1. Ensure Playwright browsers are installed: `playwright install chromium`
2. Check if Chrome is installed on your system
3. Try running with administrator privileges
4. Disable antivirus temporarily during browser launch

### Issue: "Login form not found"
**Solutions:**
1. Check your internet connection
2. Verify Instagram is accessible in your region
3. Try using a different proxy if configured
4. Clear browser cache: delete `__pycache__` folder

### Issue: "2FA verification failed"
**Solutions:**
1. Verify your TOTP secret is correct (16 or 32 characters, base32 format)
2. Check system time is synchronized
3. Test TOTP code generation manually
4. Ensure Instagram account has TOTP-based 2FA enabled

### Issue: "File upload failed"
**Solutions:**
1. Verify media file exists and is readable
2. Check file format is supported
3. Ensure file size is within Instagram limits
4. Try with a different media file

## Testing Your Setup 🧪

### 1. **Run Validation Script**
```bash
cd backend
python validate_backend.py
```

### 2. **Test Login Only**
```bash
cd backend  
python test_daily_post_login.py
```

### 3. **Full System Test**
Use the web interface to run a test with one account and simple media file.

## Performance Tips ⚡

### 1. **Concurrent Accounts**
- Start with 1-2 accounts for testing
- Gradually increase to 3-5 maximum
- Too many concurrent accounts may trigger rate limits

### 2. **Timing**
- Allow 2-5 minutes per account for posting
- Add delays between accounts if using many
- Don't run too frequently (respect Instagram's limits)

### 3. **Media Files**
- Use optimized images (under 10MB)
- Keep videos under 100MB
- Use common formats for best compatibility

## Monitoring & Logs 📊

### 1. **Real-time Logs**
Monitor the web interface for real-time progress updates

### 2. **Log Files**
Check `backend/logs/` folder for detailed script logs

### 3. **Success Indicators**
- ✅ "Login successful!"
- ✅ "File upload completed successfully!"
- ✅ "Post completed successfully!"

## Need Help? 🆘

1. **Run the validation script first**
2. **Check browser window for visual clues**
3. **Review log files for specific errors**
4. **Test with a single account first**
5. **Verify all requirements are met**

---

**Note:** This automation respects Instagram's terms of service. Use responsibly and within reasonable limits.
