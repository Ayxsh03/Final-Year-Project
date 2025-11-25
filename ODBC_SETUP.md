# ODBC Driver Setup Guide

## Issue
`Connection Failed: Can't open lib 'ODBC Driver 17 for SQL Server' : file not found`

This error means the required ODBC driver for connecting to MS SQL Server is not installed on your system.

---

## Solution

### For Local Development (macOS)

**Option 1: Install Microsoft ODBC Driver 17** (Original driver)
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql17 mssql-tools
```

**Option 2: Use FreeTDS** (Lighter alternative, same as Azure)
```bash
brew install freetds
```

After installation, update your connection string in `.env` or use the default in `verify_db.py`.

### For Azure Deployment

**Azure App Service (Linux) comes with FreeTDS pre-installed**, so no additional setup is needed! 

Just use this connection string format in Azure App Settings:
```
DATABASE_URL=Driver={FreeTDS};Server=52.172.139.167;Database=SiteSurveillance;UID=Rms;PWD=Rms_2024@#$;TDS_Version=7.4;Port=1433;
```

---

## Updated Files

- `backend/verify_db.py` - Now uses FreeTDS driver by default
- `.env.example` - Updated with MS SQL connection string examples

---

## Testing

After installing the driver, test the connection:
```bash
python backend/verify_db.py
```

Expected output:
```
Connecting to: Driver={FreeTDS};Server=52.172.139.167;...
Connection Successful!
SQL Server Version: Microsoft SQL Server ...
```

---

## Connection String Formats

### FreeTDS (Recommended for Azure)
```
Driver={FreeTDS};Server=HOST;Database=DB;UID=USER;PWD=PASS;TDS_Version=7.4;Port=1433;
```

### ODBC Driver 17 (Windows/macOS)
```
Driver={ODBC Driver 17 for SQL Server};Server=HOST;Database=DB;Uid=USER;Pwd=PASS;
```

### ODBC Driver 18 (Latest)
```
Driver={ODBC Driver 18 for SQL Server};Server=HOST;Database=DB;Uid=USER;Pwd=PASS;Encrypt=no;
```

---

## Next Steps

1. Install FreeTDS locally: `brew install freetds`
2. Test connection: `python backend/verify_db.py`
3. Push updates to GitHub
4. Azure deployment will work automatically (FreeTDS is pre-installed)
