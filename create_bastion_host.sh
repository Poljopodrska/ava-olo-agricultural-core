#!/bin/bash
# === STEP 1: CREATE EC2 BASTION HOST ===
echo "=== CREATING DATABASE BASTION HOST ==="

# First, get the VPC and subnet details we need
VPC_ID="vpc-06c1c1699aa9cd9c6"
SUBNET_ID=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[0].SubnetId' --output text --region us-east-1)

echo "Using VPC: $VPC_ID"
echo "Using Subnet: $SUBNET_ID"

# Get the latest Amazon Linux 2 AMI
AMI_ID=$(aws ec2 describe-images --owners amazon --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' --output text --region us-east-1)

echo "Using AMI: $AMI_ID"

# === STEP 2: CREATE SECURITY GROUP FOR BASTION ===
echo "Creating security group for bastion host..."

BASTION_SG=$(aws ec2 create-security-group \
  --group-name "database-bastion-sg" \
  --description "Security group for database bastion host" \
  --vpc-id $VPC_ID \
  --region us-east-1 \
  --query 'GroupId' \
  --output text)

echo "Created security group: $BASTION_SG"

# Allow SSH access from anywhere (you can restrict this to your IP later)
aws ec2 authorize-security-group-ingress \
  --group-id $BASTION_SG \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0 \
  --region us-east-1

echo "SSH access configured for bastion"

# === STEP 3: UPDATE RDS SECURITY GROUP ===
echo "Updating RDS security group to allow bastion access..."

# Add rule to RDS security group to allow access from bastion
aws ec2 authorize-security-group-ingress \
  --group-id sg-0b32106f9bc1194d8 \
  --protocol tcp \
  --port 5432 \
  --source-group $BASTION_SG \
  --region us-east-1

echo "RDS security group updated"

# === STEP 4: CREATE KEY PAIR ===
echo "Creating SSH key pair..."

aws ec2 create-key-pair \
  --key-name database-bastion-key \
  --query 'KeyMaterial' \
  --output text \
  --region us-east-1 > database-bastion-key.pem

chmod 400 database-bastion-key.pem

echo "SSH key created: database-bastion-key.pem"

# === STEP 5: LAUNCH BASTION INSTANCE ===
echo "Launching bastion host instance..."

INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.micro \
  --key-name database-bastion-key \
  --security-group-ids $BASTION_SG \
  --subnet-id $SUBNET_ID \
  --associate-public-ip-address \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=database-bastion}]' \
  --region us-east-1 \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "Bastion instance launched: $INSTANCE_ID"

# === STEP 6: WAIT FOR INSTANCE AND GET PUBLIC IP ===
echo "Waiting for instance to be running..."

aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region us-east-1

PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text \
  --region us-east-1)

echo "Bastion host ready!"
echo "Public IP: $PUBLIC_IP"

# === STEP 7: PROVIDE CONNECTION INSTRUCTIONS ===
echo ""
echo "=== BASTION HOST SETUP COMPLETE ==="
echo ""
echo "📋 CONNECTION DETAILS:"
echo "Bastion Host IP: $PUBLIC_IP"
echo "SSH Key File: database-bastion-key.pem"
echo "SSH Command: ssh -i database-bastion-key.pem ec2-user@$PUBLIC_IP"
echo ""
echo "🔧 DATABASE CONNECTION VIA SSH TUNNEL:"
echo "Database Host: farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com"
echo "Database Port: 5432"
echo "Database Name: postgres"
echo "Username: postgres"
echo "Password: 2hpzvrg_xP~qNbz1[_NppSK\$e*O1"
echo ""
echo "🎯 NEXT STEPS:"
echo "1. Download a database client (pgAdmin, DBeaver, or TablePlus)"
echo "2. Create SSH tunnel connection using the bastion host"
echo "3. Connect to your RDS database through the tunnel"
echo ""
echo "✅ Your database is now accessible securely!"