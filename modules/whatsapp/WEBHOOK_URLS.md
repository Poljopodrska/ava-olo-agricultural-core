# WhatsApp Webhook URLs for AVA OLO System

## Production Webhook URLs

Configure these URLs in your Twilio Console for WhatsApp integration:

### 1. Primary Webhook (Required)
**URL:** `http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/whatsapp/webhook`
- **Purpose:** Receives incoming WhatsApp messages
- **Method:** POST
- **Configure in:** Twilio Console > Phone Numbers > Your WhatsApp Number > "When a message comes in"

### 2. Fallback Webhook (Recommended)
**URL:** `http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/whatsapp/fallback`
- **Purpose:** Handles failed message processing
- **Method:** POST
- **Configure in:** Twilio Console > Phone Numbers > Your WhatsApp Number > "Primary handler fails"

### 3. Status Callback (Optional)
**URL:** `http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/whatsapp/status`
- **Purpose:** Receives message delivery status updates
- **Method:** POST
- **Configure in:** Twilio Console > Messaging > Settings > "Status callback URL"

## Configuration Steps

1. **Log into Twilio Console**
   - Go to https://console.twilio.com
   - Navigate to Messaging > Try it out > WhatsApp sandbox (for testing)
   - Or Phone Numbers > Your WhatsApp Number (for production)

2. **Configure Webhooks**
   - Set "When a message comes in" to the Primary Webhook URL
   - Set "Primary handler fails" to the Fallback Webhook URL
   - Save configuration

3. **Test the Integration**
   - Send a WhatsApp message to +38591857451
   - You should receive an automatic response in Croatian
   - Check `/api/v1/whatsapp/health` endpoint for status

## Available Endpoints

### Configuration Endpoint
**GET** `/api/v1/whatsapp/config`
- Returns current webhook URLs and configuration status
- Shows if Twilio credentials are configured

### Health Check
**GET** `/api/v1/whatsapp/health`
- Returns WhatsApp service health status
- Shows if integration is enabled and configured

### Diagnostic Endpoint
**GET** `/api/v1/whatsapp/diagnostic`
- Runs comprehensive diagnostics
- Returns detailed configuration and connectivity report

### Test Send Endpoint
**POST** `/api/v1/whatsapp/test-send`
- Parameters: `phone_number`, `message`
- Tests sending a WhatsApp message
- Requires Twilio to be enabled and configured

## Environment Variables Required

Configure these in your ECS task definition:

```bash
TWILIO_ENABLED=true
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+38591857451
BASE_URL=http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com
```

## Troubleshooting

1. **Webhook not receiving messages**
   - Verify webhook URL is accessible from internet
   - Check ECS service is running
   - Verify security groups allow inbound HTTP traffic

2. **Messages not sending**
   - Check Twilio credentials are configured
   - Verify phone number format (must include country code)
   - Check Twilio account has sufficient balance

3. **Signature validation failing**
   - Ensure TWILIO_AUTH_TOKEN matches your account
   - Verify webhook URL in Twilio matches exactly

## Testing with cURL

Test webhook manually:
```bash
curl -X POST http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/whatsapp/webhook \
  -d "MessageSid=TEST123" \
  -d "From=whatsapp:+359885123456" \
  -d "Body=Test message" \
  -d "To=whatsapp:+38591857451"
```

Check configuration:
```bash
curl http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/whatsapp/config
```