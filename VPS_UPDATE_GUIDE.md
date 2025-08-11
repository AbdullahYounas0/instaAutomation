# VPS Deployment Update Guide

## 🚀 How to Update Your VPS with the Latest Fixes

The latest code includes critical fixes for:
- ✅ Automatic Playwright browser installation
- ✅ Enhanced OpenAI client compatibility  
- ✅ Better error handling for production environment
- ✅ Fallback mechanisms for failed services

## Option 1: Automated Update (Recommended)

### Step 1: Upload the update script to your VPS
```bash
# On your local machine, upload the script
scp vps_update.sh user@your-vps-ip:/tmp/
```

### Step 2: Run the update script on your VPS
```bash
# SSH into your VPS
ssh user@your-vps-ip

# Make the script executable and run it
chmod +x /tmp/vps_update.sh
sudo /tmp/vps_update.sh
```

## Option 2: Manual Update

### Step 1: SSH into your VPS
```bash
ssh user@your-vps-ip
```

### Step 2: Stop services
```bash
pm2 stop all
```

### Step 3: Update code
```bash
cd /var/www/instaAutomation
git fetch origin
git reset --hard origin/main
git clean -fd
```

### Step 4: Update backend dependencies
```bash
cd /var/www/instaAutomation/backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Install Playwright browsers
```bash
python -m playwright install chromium
python ../install_browsers.py
```

### Step 6: Update frontend
```bash
cd /var/www/instaAutomation/frontend
npm install
npm run build
```

### Step 7: Restart services
```bash
cd /var/www/instaAutomation
pm2 restart all
pm2 save
```

### Step 8: Verify everything is working
```bash
pm2 status
pm2 logs
```

## 🧪 Testing the Fixes

After deployment, test the fixes:

### Test 1: Browser Installation
```bash
cd /var/www/instaAutomation/backend
source venv/bin/activate
python -c "
import asyncio
from playwright.async_api import async_playwright

async def test():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    print('✅ Browser test successful!')
    await browser.close()
    await playwright.stop()

asyncio.run(test())
"
```

### Test 2: OpenAI Client
```bash
python -c "
from instagram_dm_automation import DMAutomationEngine
engine = DMAutomationEngine()
result = engine.setup_openai_client()
print('✅ OpenAI setup successful!' if result else '❌ OpenAI setup failed')
"
```

### Test 3: Run your automation scripts
- Try running Daily Post automation
- Try running DM automation  
- Try running Warmup scripts

## 🔍 Monitoring

After deployment, monitor:
- `pm2 logs` - Check for any errors
- `pm2 status` - Ensure services are running
- Your application logs for successful operations

## 🆘 Troubleshooting

If you encounter issues:

1. **Browser issues**: Run `python install_browsers.py` manually
2. **OpenAI issues**: Check the logs - it should use fallback messages if AI fails
3. **Service issues**: Restart with `pm2 restart all`
4. **Persistent issues**: Check `pm2 logs` for detailed error messages

## 📞 Support

The scripts now include automatic error recovery:
- Browser installation happens automatically when needed
- OpenAI client failures use fallback messages
- Better logging for troubleshooting

Your Instagram automation should now work reliably in production! 🎉
