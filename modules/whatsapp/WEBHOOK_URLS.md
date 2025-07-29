# WhatsApp Webhook URLs for Twilio Configuration

## Production URLs (After Deployment)

### Primary Webhook URL
```
http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com/api/v1/whatsapp/webhook
```

### Fallback Webhook URL
```
http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com/api/v1/whatsapp/fallback
```

### Status Callback URL
```
http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com/api/v1/whatsapp/status
```

### Configuration Endpoint
```
http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com/api/v1/whatsapp/config
```

### Test Endpoint
```
http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com/api/v1/whatsapp/test
```

### Health Check
```
http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com/api/v1/whatsapp/health
```

## How to Configure in Twilio

1. **Log into Twilio Console**
   - URL: https://console.twilio.com
   - Navigate to: Messaging → Senders → WhatsApp senders

2. **Select Your WhatsApp Number**
   - Click on your WhatsApp number (+385919857451)
   - Or use sandbox for testing

3. **Configure Webhooks**
   - **When a message comes in**: Paste the Primary Webhook URL
   - **Primary handler fails**: Paste the Fallback Webhook URL
   - **Status callback URL**: Paste the Status Callback URL

4. **Save Configuration**
   - Click "Save" at the bottom of the page

## Testing the Webhooks

### 1. Check Configuration
```bash
curl http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com/api/v1/whatsapp/config
```

### 2. Test Endpoint
```bash
curl -X POST http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com/api/v1/whatsapp/test
```

### 3. Health Check
```bash
curl http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com/api/v1/whatsapp/health
```

## Environment Variables Needed

Add these to AWS Secrets Manager or ECS Task Definition:

```
TWILIO_ACCOUNT_SID=[Your Account SID]
TWILIO_AUTH_TOKEN=[Your Auth Token]
TWILIO_WHATSAPP_NUMBER=whatsapp:+385919857451
BASE_URL=http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com
```

## Message Flow

1. User sends WhatsApp message to +385919857451
2. Twilio receives the message
3. Twilio sends POST request to webhook URL
4. AVA OLO webhook handler:
   - Validates Twilio signature
   - Stores message in database
   - Sends auto-response
5. User receives confirmation message

## Troubleshooting

### Webhook Not Receiving Messages
- Check if service is deployed and running
- Verify environment variables are set
- Check ALB health status
- Look at CloudWatch logs

### Signature Validation Failing
- Ensure TWILIO_AUTH_TOKEN is correct
- Check BASE_URL matches exactly
- Verify webhook URL in Twilio matches deployment

### Database Connection Issues
- Check DATABASE_URL is set correctly
- Verify RDS security group allows ECS access
- Check database credentials

## Next Steps

1. Deploy this code to ECS
2. Verify endpoints are accessible
3. Configure webhooks in Twilio
4. Send test WhatsApp message
5. Monitor CloudWatch logs