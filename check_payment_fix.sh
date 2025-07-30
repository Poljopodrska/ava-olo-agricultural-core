#!/bin/bash

echo "🔍 Checking AVA OLO Payment System Fix Status"
echo "============================================"
echo ""

# Check health endpoint
echo "1. Checking health endpoint..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://avaolo.com/api/v1/health)
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo "   ✅ Health check passed (HTTP $HEALTH_RESPONSE)"
else
    echo "   ❌ Health check failed (HTTP $HEALTH_RESPONSE)"
fi

# Check payment endpoint
echo ""
echo "2. Checking payment subscribe endpoint..."
PAYMENT_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "https://avaolo.com/api/v1/payment/subscribe?farmer_id=1")
if [ "$PAYMENT_RESPONSE" = "302" ] || [ "$PAYMENT_RESPONSE" = "303" ]; then
    echo "   ✅ Payment endpoint working (HTTP $PAYMENT_RESPONSE - Redirect to Stripe)"
elif [ "$PAYMENT_RESPONSE" = "200" ]; then
    echo "   ✅ Payment endpoint accessible (HTTP $PAYMENT_RESPONSE)"
elif [ "$PAYMENT_RESPONSE" = "500" ]; then
    echo "   ❌ Payment endpoint still failing (HTTP 500 - Stripe package may not be deployed yet)"
else
    echo "   ⚠️  Payment endpoint returned HTTP $PAYMENT_RESPONSE"
fi

# Get redirect URL if available
echo ""
echo "3. Getting Stripe checkout URL..."
STRIPE_URL=$(curl -s -i "https://avaolo.com/api/v1/payment/subscribe?farmer_id=1" | grep -i location | cut -d' ' -f2)
if [[ $STRIPE_URL == *"checkout.stripe.com"* ]]; then
    echo "   ✅ Stripe integration working!"
    echo "   Checkout URL: $STRIPE_URL"
else
    echo "   ⚠️  Could not retrieve Stripe checkout URL"
fi

echo ""
echo "============================================"
echo "📝 Summary:"
if [ "$PAYMENT_RESPONSE" = "302" ] || [ "$PAYMENT_RESPONSE" = "303" ]; then
    echo "✅ PAYMENT SYSTEM FIXED! The stripe package is now installed and working."
    echo "Peter can now test the payment flow."
elif [ "$PAYMENT_RESPONSE" = "500" ]; then
    echo "⏳ Deployment may still be in progress. Wait a few minutes and run this script again."
    echo "Check build status at: https://github.com/Poljopodrska/ava-olo-agricultural-core/actions"
else
    echo "⚠️  Payment system status unclear. Manual verification needed."
fi