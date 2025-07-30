#!/bin/bash
# AVA OLO HTTPS Setup for Application Load Balancers
# This script configures HTTPS with automatic HTTP->HTTPS redirect

set -e

echo "🔒 AVA OLO HTTPS Setup for ALBs"
echo "================================"

# Configuration
DOMAIN="ava-olo.hr"
ALB_NAMES=("ava-agricultural-alb" "ava-monitoring-alb")
REGION="us-east-1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Request SSL Certificate
echo_info "Step 1: Requesting SSL Certificate for *.$DOMAIN"

CERT_ARN=$(aws acm request-certificate \
    --domain-name "*.$DOMAIN" \
    --validation-method DNS \
    --region $REGION \
    --query 'CertificateArn' \
    --output text 2>/dev/null || echo "")

if [ ! -z "$CERT_ARN" ]; then
    echo_info "Certificate requested: $CERT_ARN"
    echo_warn "IMPORTANT: You must validate this certificate in Route53 before proceeding"
    echo_warn "Check AWS Console > Certificate Manager > $CERT_ARN"
    echo ""
    read -p "Press Enter after validating the certificate..."
else
    echo_info "Certificate may already exist, listing existing certificates..."
    aws acm list-certificates --region $REGION --query 'CertificateSummaryList[?DomainName==`*.ava-olo.hr`]'
    read -p "Enter the Certificate ARN to use: " CERT_ARN
fi

# Verify certificate is validated
echo_info "Checking certificate status..."
CERT_STATUS=$(aws acm describe-certificate \
    --certificate-arn $CERT_ARN \
    --region $REGION \
    --query 'Certificate.Status' \
    --output text)

if [ "$CERT_STATUS" != "ISSUED" ]; then
    echo_error "Certificate is not yet issued (Status: $CERT_STATUS)"
    echo_warn "Please wait for DNS validation to complete"
    exit 1
fi

echo_info "Certificate is ready (Status: $CERT_STATUS)"

# Step 2: Configure each ALB
for ALB_NAME in "${ALB_NAMES[@]}"; do
    echo_info "Configuring HTTPS for $ALB_NAME"
    
    # Get ALB ARN
    ALB_ARN=$(aws elbv2 describe-load-balancers \
        --names $ALB_NAME \
        --region $REGION \
        --query 'LoadBalancers[0].LoadBalancerArn' \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$ALB_ARN" ] || [ "$ALB_ARN" == "None" ]; then
        echo_warn "ALB $ALB_NAME not found, skipping..."
        continue
    fi
    
    echo_info "Found ALB: $ALB_ARN"
    
    # Get existing HTTP listener
    HTTP_LISTENER_ARN=$(aws elbv2 describe-listeners \
        --load-balancer-arn $ALB_ARN \
        --region $REGION \
        --query 'Listeners[?Port==`80`].ListenerArn' \
        --output text)
    
    # Get target group ARN from HTTP listener
    TARGET_GROUP_ARN=$(aws elbv2 describe-listeners \
        --load-balancer-arn $ALB_ARN \
        --region $REGION \
        --query 'Listeners[?Port==`80`].DefaultActions[0].TargetGroupArn' \
        --output text)
    
    if [ -z "$TARGET_GROUP_ARN" ] || [ "$TARGET_GROUP_ARN" == "None" ]; then
        echo_error "Could not find target group for $ALB_NAME"
        continue
    fi
    
    echo_info "Target Group: $TARGET_GROUP_ARN"
    
    # Step 2a: Create HTTPS listener (port 443)
    echo_info "Creating HTTPS listener on port 443..."
    
    HTTPS_LISTENER_ARN=$(aws elbv2 create-listener \
        --load-balancer-arn $ALB_ARN \
        --protocol HTTPS \
        --port 443 \
        --certificates CertificateArn=$CERT_ARN \
        --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN \
        --region $REGION \
        --query 'Listeners[0].ListenerArn' \
        --output text 2>/dev/null || echo "")
    
    if [ ! -z "$HTTPS_LISTENER_ARN" ] && [ "$HTTPS_LISTENER_ARN" != "None" ]; then
        echo_info "HTTPS listener created: $HTTPS_LISTENER_ARN"
    else
        echo_warn "HTTPS listener may already exist for $ALB_NAME"
    fi
    
    # Step 2b: Modify HTTP listener to redirect to HTTPS
    echo_info "Configuring HTTP->HTTPS redirect..."
    
    if [ ! -z "$HTTP_LISTENER_ARN" ] && [ "$HTTP_LISTENER_ARN" != "None" ]; then
        aws elbv2 modify-listener \
            --listener-arn $HTTP_LISTENER_ARN \
            --default-actions Type=redirect,RedirectConfig="{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}" \
            --region $REGION > /dev/null
        
        echo_info "HTTP->HTTPS redirect configured for $ALB_NAME"
    else
        echo_warn "HTTP listener not found for $ALB_NAME"
    fi
    
    # Get ALB DNS name for testing
    ALB_DNS=$(aws elbv2 describe-load-balancers \
        --load-balancer-arn $ALB_ARN \
        --region $REGION \
        --query 'LoadBalancers[0].DNSName' \
        --output text)
    
    echo_info "ALB DNS: $ALB_DNS"
    echo ""
done

# Step 3: Test Configuration
echo_info "Step 3: Testing HTTPS Configuration"
echo ""

for ALB_NAME in "${ALB_NAMES[@]}"; do
    ALB_DNS=$(aws elbv2 describe-load-balancers \
        --names $ALB_NAME \
        --region $REGION \
        --query 'LoadBalancers[0].DNSName' \
        --output text 2>/dev/null || echo "")
    
    if [ ! -z "$ALB_DNS" ] && [ "$ALB_DNS" != "None" ]; then
        echo_info "Testing $ALB_NAME at $ALB_DNS"
        echo "  HTTPS: https://$ALB_DNS/health"
        echo "  HTTP redirect: http://$ALB_DNS/health (should redirect to HTTPS)"
        echo ""
    fi
done

echo_info "HTTPS setup completed!"
echo ""
echo_warn "Next Steps:"
echo "1. Update Route53 records to point to ALB DNS names"
echo "2. Test both HTTP and HTTPS endpoints"
echo "3. Update application URLs to use HTTPS"
echo "4. Set HTTPS_ONLY=true in environment variables"
echo ""
echo_info "Security Headers will be added automatically by the applications"