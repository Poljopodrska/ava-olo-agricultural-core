# Connecting WSL2 to Windows PostgreSQL

## Current Situation
- Windows PostgreSQL is running with database `farmer_crm` containing 4 real farmers
- WSL2 cannot connect due to network configuration
- Password: Podrska2025!

## Option 1: Enable Windows PostgreSQL for WSL2 Access

### Step 1: Configure PostgreSQL to Accept Connections
1. Open Windows PowerShell as Administrator
2. Edit PostgreSQL configuration:
```powershell
notepad "C:\Program Files\PostgreSQL\16\data\postgresql.conf"
```
3. Find and modify:
```
listen_addresses = '*'  # or '172.26.16.1,localhost'
```

### Step 2: Configure Authentication
1. Edit pg_hba.conf:
```powershell
notepad "C:\Program Files\PostgreSQL\16\data\pg_hba.conf"
```
2. Add this line:
```
host    all             all             172.26.16.0/20          md5
```

### Step 3: Restart PostgreSQL
```powershell
net stop postgresql-x64-16
net start postgresql-x64-16
```

### Step 4: Configure Windows Firewall
1. Open Windows Defender Firewall
2. Add inbound rule for port 5432
3. Allow connections from WSL2 subnet (172.26.16.0/20)

## Option 2: Use SSH Tunnel (Simpler)
From WSL2:
```bash
ssh -L 5432:localhost:5432 user@windows_host
```

## Option 3: Export/Import Data
1. From Windows PowerShell:
```powershell
pg_dump -h localhost -U postgres -d farmer_crm > farmer_crm_backup.sql
```

2. Copy to WSL2 and import:
```bash
psql -h localhost -U postgres -c "CREATE DATABASE farmer_crm"
psql -h localhost -U postgres -d farmer_crm < /mnt/c/path/to/farmer_crm_backup.sql
```

## Testing Connection
Once configured, test with:
```bash
psql -h 172.26.16.1 -U postgres -d farmer_crm -c "SELECT COUNT(*) FROM farmers"
```