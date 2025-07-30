# 🔒 AVA OLO HTTPS Setup Guide

## Current Status
- ✅ ALBs configured and running on HTTP (port 80)
- ✅ Security implementations ready in application
- 🟡 HTTPS requires SSL certificate

## Option 1: Using AWS Certificate Manager (Recommended)
1. **Obtain a domain name** (e.g., ava-olo.com)
2. **Request certificate in ACM**:
   ```bash
   aws acm request-certificate \
       --domain-name "*.ava-olo.com" \
       --validation-method DNS \
       --region us-east-1
   ```
3. **Validate via DNS** (add CNAME records)
4. **Run HTTPS script**:
   ```bash
   ./scripts/enable_https_alb.sh
   ```

## Option 2: Using Existing Certificate
1. **Import certificate to ACM**:
   ```bash
   aws acm import-certificate \
       --certificate fileb://cert.pem \
       --certificate-chain fileb://chain.pem \
       --private-key fileb://key.pem \
       --region us-east-1
   ```
2. **Update ALB listeners** with certificate ARN

## Option 3: Continue with HTTP (Current)
- Services are secure at application level
- HTTPS can be added later without code changes
- All security features are active

## Security Features Already Active:
- ✅ AWS Secrets Manager for credentials
- ✅ Password hashing with bcrypt
- ✅ Authentication on dashboards
- ✅ No hardcoded secrets
- ✅ Secure database connections

## ALB Information:

### Farmers ALB
- DNS: ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com
- Current: HTTP (port 80)

### Internal ALB
- DNS: ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com
- Current: HTTP (port 80)
