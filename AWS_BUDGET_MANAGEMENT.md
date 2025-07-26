# AWS Budget Management Guide

## Overview
This document outlines the AWS budget configuration for the AVA OLO platform, including alert thresholds, notification settings, and cost management best practices.

## Budget Configuration

### Budget Details
- **Budget Name**: AVA-OLO-Monthly-Budget
- **Monthly Limit**: $440 USD (approximately €400 EUR)
- **Budget Type**: Cost Budget
- **Time Period**: Monthly (resets on the 1st of each month)
- **Created**: July 20, 2025

### Cost Types Included
- ✅ Tax
- ✅ Subscriptions
- ✅ Upfront costs
- ✅ Recurring costs
- ✅ Support costs
- ✅ Other subscriptions
- ✅ Discounts
- ❌ Credits (excluded)
- ❌ Refunds (excluded)

## Alert Configuration

### Alert Thresholds
1. **Warning Alert (80%)**
   - Threshold: $352 USD
   - Type: Actual spend
   - Action: Email notification

2. **Critical Alert (100%)**
   - Threshold: $440 USD
   - Type: Actual spend
   - Action: Email notification

### Notification Recipients
- Primary: knaflicpeter@gmail.com
- Additional recipients can be added through AWS Budgets console

## Monitoring and Tracking

### How to Check Budget Status
```bash
# View current budget status
aws budgets describe-budgets --account-id 127679825789

# Get budget performance
aws budgets describe-budget-performance-history \
  --account-id 127679825789 \
  --budget-name AVA-OLO-Monthly-Budget
```

### AWS Console Access
1. Navigate to AWS Billing Dashboard
2. Click on "Budgets" in the left menu
3. Select "AVA-OLO-Monthly-Budget"
4. View current spend, forecasted spend, and alerts

## Cost Management Best Practices

### Daily Monitoring
- Check daily spend trends
- Current daily average: $5-10 USD
- Target daily spend: <$14 USD

### Weekly Reviews
- Review top cost drivers
- Identify any anomalies
- Check for unused resources

### Monthly Actions
- Analyze cost report
- Optimize based on usage patterns
- Review and adjust budget if needed

## Alert Response Procedures

### When 80% Alert Triggers ($352)
1. Review current spend breakdown
2. Identify top cost drivers
3. Implement immediate optimizations:
   - Stop non-critical services
   - Reduce instance sizes if possible
   - Clean up unused resources
4. Project end-of-month spend

### When 100% Alert Triggers ($440)
1. **Immediate Actions**:
   - Stop all non-production services
   - Disable auto-scaling
   - Review and stop development environments
2. **Communication**:
   - Notify stakeholders
   - Plan for budget adjustment if needed
3. **Prevention**:
   - Implement stricter resource controls
   - Review architecture for cost optimization

## Cost Optimization Checklist

### Weekly Tasks
- [ ] Review running instances
- [ ] Check for unattached EBS volumes
- [ ] Verify all Elastic IPs are in use
- [ ] Review CloudWatch logs retention
- [ ] Check for idle RDS instances

### Monthly Tasks
- [ ] Analyze cost report
- [ ] Review and optimize instance types
- [ ] Clean up old snapshots
- [ ] Review data transfer costs
- [ ] Update budget forecasts

## Budget Modification

### To Update Budget Limit
```bash
aws budgets update-budget \
  --account-id 127679825789 \
  --new-budget file://updated_budget.json
```

### To Add Recipients
```bash
aws budgets update-budget-action \
  --account-id 127679825789 \
  --budget-name AVA-OLO-Monthly-Budget \
  --action-id [ACTION_ID] \
  --subscribers SubscriptionType=EMAIL,Address=new@email.com
```

## Cost Saving Opportunities

### Implemented
- ✅ Removed redundant ALB (saving ~$20/month)
- ✅ Consolidated infrastructure
- ✅ Set up proactive alerts

### Planned
- Review ElastiCache usage ($11/month potential)
- Optimize CloudWatch logs ($4/month potential)
- Right-size RDS instance ($5-10/month potential)
- Review ECS configuration ($5/month potential)

## Reporting

### Monthly Cost Report Location
- File: `AWS_COST_REPORT.md`
- Updated: Monthly
- Contains: Detailed breakdown and recommendations

### Key Metrics to Track
1. Total monthly spend
2. Daily average cost
3. Service-wise breakdown
4. Month-over-month growth
5. Budget utilization percentage

## Emergency Contacts

### Budget Alerts
- Primary: knaflicpeter@gmail.com
- AWS Support: Via AWS Console

### Escalation Path
1. Email alert to configured address
2. Review in AWS Console
3. Implement cost controls
4. Contact AWS Support if needed

## Additional Resources

- [AWS Cost Management Best Practices](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-best-practices.html)
- [AWS Budgets Documentation](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)
- [Cost Optimization Pillar](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html)

---

*Last Updated: July 20, 2025*