# Railway Fix Instructions for @Astraro_bot

## Problem
Webhook was returning 500 Internal Server Error because:
1. No error handling in webhook handler
2. WEBHOOK_SECRET not configured in Railway (code generates random secret on each restart)

## Solutions Applied

### 1. Code Fix (DONE ✅)
Added try-except and logging to webhook handler in `src/main.py`:
- Catches all exceptions
- Logs errors for debugging
- Returns 200 to prevent Telegram from disabling webhook
- Committed: d5a6d93

### 2. Webhook Secret Fix (NEEDS MANUAL ACTION ⚠️)

**Current state:**
- Telegram webhook set with secret: `E0SnFK8Wl4NyQ0oqV-ufqdB12m_tF19Xenzvkptn27c`
- Code generates random secret on each restart
- Status: webhook returns 401 (unauthorized) but doesn't crash anymore

**Action required:**
1. Open Railway dashboard: https://railway.app/project/19735644-3520-43fa-adbd-8728403c7c76
2. Select service "AdtroBot"
3. Go to "Variables" tab
4. Add new variable:
   - Name: `WEBHOOK_SECRET`
   - Value: `E0SnFK8Wl4NyQ0oqV-ufqdB12m_tF19Xenzvkptn27c`
5. Click "Add" then save
6. Redeploy the service

**Alternative (via Railway CLI):**
```bash
cd /Users/kirill/.openclaw/workspace/AdtroBot
railway link  # Follow prompts to link project
railway variables --set "WEBHOOK_SECRET=E0SnFK8Wl4NyQ0oqV-ufqdB12m_tF19Xenzvkptn27c"
```

## Verification

After adding WEBHOOK_SECRET to Railway:

```bash
# 1. Check webhook status
curl "https://api.telegram.org/bot8536561563:AAFRd_4h-4hWzMrxrd1SjP6a9IfsPJ67NBw/getWebhookInfo" | jq '.result | {url, last_error_date, last_error_message}'

# Should show: last_error_date: null, last_error_message: null

# 2. Test webhook directly
curl -X POST "https://adtrobot-production.up.railway.app/webhook" \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Bot-Api-Secret-Token: E0SnFK8Wl4NyQ0oqV-ufqdB12m_tF19Xenzvkptn27c" \
  -d '{"update_id": 1, "message": {"message_id": 1, "date": 1234567890, "chat": {"id": 123, "type": "private"}, "text": "/start"}}'

# Should return: HTTP 200 (not 401)

# 3. Send test message to bot
# Open @Astraro_bot in Telegram and send /start
```

## Summary

✅ Fixed: Webhook error handling
✅ Fixed: Telegram webhook updated with known secret
⚠️ TODO: Add WEBHOOK_SECRET to Railway env vars
⚠️ TODO: Redeploy after adding env var
⚠️ TODO: Test bot with real message

**Current status:** Bot is partially working (doesn't crash), but webhook auth will fail until WEBHOOK_SECRET is set in Railway.
