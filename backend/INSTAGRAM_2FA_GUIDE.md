# Instagram 2FA (T2. Open Instagram app on mobile device
3. Go to Settings → Privacy and Security → Two-Factor Authentication
4. Enable "Authentication App" option
5. When presented with QR code, also note down the text secret key (32-character base32 string)
6. Example secret: `JPV6WXN4CTU5TSQO3TRK7AWE2Z3XZIOP`
7. Or formatted with spaces: `JPV6 WXN4 CTU5 TSQO 3TRK 7AWE 2Z3X ZIOP`Implementation Guide

## Overview

The Instagram automation system now supports automatic Two-Factor Authentication (2FA) using Google Authenticator TOTP (Time-based One-Time Password) codes. This allows the system to automatically handle 2FA prompts during login without manual intervention.

## Features

✅ **Automatic 2FA Detection**: Detects when Instagram requires 2FA verification
✅ **TOTP Code Generation**: Generates Google Authenticator compatible codes
✅ **Non-blocking Operation**: Works in parallel across multiple accounts
✅ **Error Handling**: Retries failed 2FA attempts and provides clear logging
✅ **Secure Storage**: TOTP secrets are stored securely per account

## Setup Instructions

### 1. Enable 2FA on Instagram Account

1. Open Instagram app on mobile device
2. Go to Settings → Privacy and Security → Two-Factor Authentication
3. Enable "Authentication App" option
4. When presented with QR code, also note down the text secret key (16-character base32 string)
5. Example secret: `JBSWY3DPEHPK3PXP`

### 2. Add TOTP Secret to Account

#### Via Admin Panel (Recommended):
1. Login to admin dashboard
2. Navigate to Instagram Accounts management
3. When adding/editing an account, fill in the "TOTP Secret" field
4. Use the 32-character base32 string from Instagram setup
5. Can include spaces for readability: `JPV6 WXN4 CTU5 TSQO 3TRK 7AWE 2Z3X ZIOP`

#### Via CSV/Excel Import:
Add a `totp_secret` column to your accounts file:
```csv
username,password,email,phone,notes,totp_secret
myuser1,mypass1,email1@test.com,+1234567890,Notes here,JPV6WXN4CTU5TSQO3TRK7AWE2Z3XZIOP
myuser2,mypass2,email2@test.com,+1234567891,More notes,ABCD1234EFGH5678IJKL9012MNOP34QR
```

### 3. API Endpoints

The following endpoints support TOTP secrets:

- `POST /api/instagram-accounts` - Add account with TOTP secret
- `PUT /api/instagram-accounts/{id}` - Update account TOTP secret  
- `POST /api/instagram-accounts/import` - Import accounts with TOTP secrets

## How It Works

### During Login Process:

1. **Normal Login**: System attempts regular username/password login
2. **2FA Detection**: If Instagram shows 2FA prompt, system detects it automatically
3. **TOTP Generation**: System generates current TOTP code using stored secret
4. **Auto-Fill**: Code is automatically entered into the verification field
5. **Submission**: System submits the 2FA form automatically
6. **Retry Logic**: If first attempt fails, waits 30 seconds and retries with new code
7. **Success/Failure**: Clear logging indicates success or failure per account

### Supported 2FA Elements:

The system can handle these Instagram 2FA selectors:
- `input[name="verificationCode"]`
- `input[aria-label="Security Code"]`
- `input[type="tel"][maxlength="8"]`
- Confirm/Submit buttons

### Parallel Processing:

- Each account runs in its own browser session
- TOTP codes are generated independently per account
- No conflicts between parallel sessions
- Works with up to 10 parallel accounts

## Error Handling

### Common Scenarios:

| Scenario | System Response |
|----------|-----------------|
| No TOTP Secret | Logs error, skips account |
| Invalid TOTP Secret | Logs error, skips account |
| 2FA Field Not Found | Logs error, retries |
| First TOTP Fails | Waits 30s, retries with new code |
| Both TOTP Attempts Fail | Logs error, skips account |

### Log Messages:

```
[username] 2FA verification detected - attempting automatic resolution
[username] Generated TOTP code: 123456
[username] ✅ 2FA verification successful!
[username] ❌ 2FA verification failed after retry
```

## Security Considerations

### TOTP Secret Storage:
- Secrets are 32-character base32 strings (or 16-char for older Instagram accounts)
- Can include spaces for readability: `JPV6 WXN4 CTU5 TSQO 3TRK 7AWE 2Z3X ZIOP`
- Stored in `instagram_accounts.json` - consider encrypting in production
- Rotate secrets periodically for enhanced security

### Rate Limiting:
- Instagram may rate limit excessive 2FA attempts
- System waits 30 seconds between retry attempts
- Failed accounts are skipped to avoid lockouts

## Testing

### Test TOTP Generation:
```bash
cd backend
python test_2fa.py
```

### Manual Test with Sample Account:
1. Add account with TOTP secret: `JBSWY3DPEHPK3PXP`
2. Run DM automation with visual mode
3. Observe 2FA handling in browser window

## Troubleshooting

### Issue: "No TOTP secret configured"
**Solution**: Add the 16-character base32 secret to the account

### Issue: "2FA verification failed"
**Solution**: 
1. Verify the TOTP secret is correct
2. Check if Instagram changed 2FA UI
3. Try with a different account

### Issue: "Could not find verification code input field"
**Solution**: Instagram may have updated their UI. Check console logs for current selectors.

## Migration Guide

### Existing Accounts:
1. All existing accounts continue to work without TOTP secrets
2. Add TOTP secrets gradually as accounts get 2FA enabled
3. No breaking changes to existing functionality

### Backward Compatibility:
- Accounts without TOTP secrets work normally
- System gracefully handles missing TOTP secrets
- No changes required to existing workflows

## Support

For issues or questions about 2FA implementation:
1. Check the log files for detailed error messages
2. Run the test script to verify TOTP functionality
3. Ensure Instagram account has 2FA properly configured
4. Contact support with specific error messages and account details (without secrets)

---

**Note**: Keep TOTP secrets secure and never share them. Each secret is unique to one Instagram account and should be stored safely.
