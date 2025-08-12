# VPS Update Commands

## 🚀 Update Your VPS with the Latest Authentication Fixes

Use these commands to pull the latest changes from GitHub to your VPS:

### 1. Connect to Your VPS
```bash
ssh your-username@your-vps-ip
```

### 2. Navigate to Your Project Directory
```bash
cd /path/to/your/instaAutomation  # Replace with your actual path
```

### 3. Pull the Latest Changes from GitHub
```bash
git pull origin main
```

### 4. Check What Files Were Updated
```bash
git log --oneline -1
git diff HEAD~1 --name-only
```

### 5. Restart Your Application (if running as a service)
```bash
# If using PM2
pm2 restart all

# Or if using systemd
sudo systemctl restart your-service-name

# Or if running manually, stop and restart your application
```

### 6. Verify the Updates
```bash
# Check if the test file exists
ls -la backend/test_auth_fixes.py

# Test the authentication fixes
cd backend
python test_auth_fixes.py
```

### 7. Monitor Logs
```bash
# If using PM2
pm2 logs

# Or check your application logs
tail -f /path/to/your/logs/app.log
```

## 📋 Files Updated in This Push

✅ **backend/enhanced_instagram_auth.py** - Enhanced password detection and cookie management
✅ **backend/instagram_cookie_manager.py** - Fixed recursion bug and extended timeouts  
✅ **backend/instagram_daily_post.py** - Set headless mode for VPS
✅ **VPS_AUTHENTICATION_FIXES.md** - Documentation of all fixes
✅ **backend/test_auth_fixes.py** - Test script for authentication

## 🔍 Expected Improvements

After updating your VPS, you should see:

1. **Better Cookie Recognition** - Existing cookies should be used properly
2. **Improved Password Detection** - Login forms should be detected more reliably
3. **VPS-Optimized Browser** - Headless mode with no screenshot issues
4. **Extended Session Timeouts** - 72-hour sessions with 48-hour grace period
5. **Better Error Logging** - More detailed debugging information

## 🧪 Testing After Update

Run this command on your VPS to test the fixes:

```bash
cd backend
python test_auth_fixes.py
```

You should see output like:
```
✅ Found 1 stored accounts:
  • paulpmoorenoco09f: ✅ Valid
    - Has sessionid: True
    - Has csrftoken: True
```

## 🚨 If You Encounter Issues

1. **Check Python dependencies**: `pip install -r requirements.txt`
2. **Verify Playwright browsers**: `playwright install chromium`
3. **Check file permissions**: `chmod +x your-script-files`
4. **Review logs**: Look for any new error messages in your application logs

## 📞 Next Steps

1. Update your VPS using the commands above
2. Test the daily post script with a single account first
3. Monitor the logs for any remaining issues
4. If successful, run with all accounts

The main authentication issues should now be resolved! 🎉
