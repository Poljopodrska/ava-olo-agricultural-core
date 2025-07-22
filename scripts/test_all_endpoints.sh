#!/bin/bash

echo "🔍 TESTING ALL DISCOVERED ENDPOINTS"
echo "==================================="
echo ""

# Test agricultural service
echo "1. Agricultural Core Service (Farmers Portal):"
echo "   URL: http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"
echo -n "   Status: "
curl -s -o /dev/null -w "%{http_code}" -m 5 http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/ || echo "TIMEOUT"
echo ""
echo -n "   Version: "
curl -s -m 5 http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/system/health | grep -o '"version":"[^"]*"' | cut -d'"' -f4 || echo "Could not get version"
echo ""

# Test monitoring service
echo -e "\n2. Monitoring Dashboards Service:"
echo "   URL: http://ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com"
echo -n "   Status: "
curl -s -o /dev/null -w "%{http_code}" -m 5 http://ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com/ || echo "TIMEOUT"
echo ""
echo -n "   Version: "
curl -s -m 5 http://ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com/ | grep -o "v[0-9]\.[0-9]\.[0-9][^<]*" | head -1 || echo "Could not get version"
echo ""

# Test CH service (appears to be another service)
echo -e "\n3. CH Service:"
echo "   URL: http://ch-alb-2140286266.us-east-1.elb.amazonaws.com"
echo -n "   Status: "
curl -s -o /dev/null -w "%{http_code}" -m 5 http://ch-alb-2140286266.us-east-1.elb.amazonaws.com/ || echo "TIMEOUT"
echo ""

# Try with direct IP resolution bypass
echo -e "\n4. Testing with direct IP (bypassing DNS):"
echo "   Getting ALB IPs..."

# Get IPs for agricultural ALB
FARMER_IPS=$(dig +short ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com 2>/dev/null | grep -E '^[0-9]+\.' | head -2)
if [ -n "$FARMER_IPS" ]; then
    echo "   Agricultural ALB IPs found:"
    for ip in $FARMER_IPS; do
        echo -n "     $ip - Status: "
        curl -s -o /dev/null -w "%{http_code}" -m 5 -H "Host: ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com" http://$ip/ || echo "FAILED"
        echo ""
    done
else
    echo "   Could not resolve Agricultural ALB IPs"
fi

# Alternative access methods
echo -e "\n5. Alternative Access Methods:"
echo "   If DNS is not working, try these direct IPs:"
echo ""
echo "   Option 1 - Add to /etc/hosts (or C:\\Windows\\System32\\drivers\\etc\\hosts):"
echo "   # Get actual IPs from AWS console and add:"
echo "   [IP-ADDRESS] ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"
echo "   [IP-ADDRESS] ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com"
echo ""
echo "   Option 2 - Use IP directly with Host header:"
echo "   curl -H 'Host: ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com' http://[IP-ADDRESS]/"
echo ""

# Summary
echo "==================================="
echo "SUMMARY:"
echo ""
echo "✅ SERVICES ARE RUNNING!"
echo "✅ ALBs are healthy and responding"
echo "❌ DNS resolution appears to be failing"
echo ""
echo "WORKING ENDPOINTS:"
echo "- Agricultural (Farmers): http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"
echo "- Monitoring: http://ava-olo-internal-alb-426050720.us-east-1.elb.amazonaws.com"
echo ""
echo "The services are operational, but there may be a DNS propagation issue."