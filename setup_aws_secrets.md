# Setting Up AWS Secrets Manager for AVA OLO

## Step 1: Create the Secret in AWS Console

1. **Go to AWS Secrets Manager**
   - Search for "Secrets Manager" in AWS Console
   - Click "Store a new secret"

2. **Choose Secret Type**
   - Select: "Other type of secret"
   - Choose "Key/value" format

3. **Enter These Key/Value Pairs**
   ```
   DB_HOST: farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com
   DB_NAME: farmer_crm
   DB_USER: postgres
   DB_PASSWORD: [PASTE THE ACTUAL PASSWORD HERE]
   DB_PORT: 5432
   JWT_SECRET: constitutional-ava-olo-production-secret-key-2024
   ```

4. **Name Your Secret**
   - Secret name: `ava-olo/agricultural-core/production`
   - Description: "AVA OLO Agricultural Core Production Credentials"

5. **Save the Secret**
   - Note the ARN (you'll need it)

## Step 2: Update App Runner to Use Secrets

1. **In App Runner Console**
   - Go to your service configuration
   - Click "Edit service"

2. **Add IAM Role Permission**
   - The App Runner service needs permission to read the secret
   - Add this policy to the service role:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "secretsmanager:GetSecretValue"
         ],
         "Resource": "arn:aws:secretsmanager:us-east-1:*:secret:ava-olo/agricultural-core/production-*"
       }
     ]
   }
   ```

3. **Update Environment Variables**
   - Remove the hardcoded DB_PASSWORD
   - Add: `AWS_SECRET_NAME: ava-olo/agricultural-core/production`

## Step 3: I'll Update the Code

Once you've created the secret, I'll update the code to:
- Read from AWS Secrets Manager
- Parse the credentials
- Use them for database connection

## Step 4: The Password

**PASTE THE PASSWORD IN THE AWS CONSOLE**, not here. The password is:
```
2hpzvrg_xP~qNbz1[_NppSK$e*O1
```

## Why This Is Better

✅ **No special character issues** - AWS handles it properly
✅ **More secure** - Credentials not in code or environment variables
✅ **Rotation support** - Can change passwords without redeploying
✅ **Audit trail** - AWS logs all access to secrets
✅ **Production best practice** - How real applications handle credentials

Let me know when you've created the secret, and I'll update the code!