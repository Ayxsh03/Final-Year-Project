import asyncio
import os
import aioodbc



# Connection string - tries FreeTDS library path first, then ODBC Driver 17
DATABASE_URL = os.getenv("DATABASE_URL") or (
    # Option 1: Direct FreeTDS library path (works on macOS without ODBC registration)
    "DRIVER=/opt/homebrew/lib/libtdsodbc.so;"
    "Server=52.172.139.167;"
    "Database=SiteSurveillance;"
    "UID=Rms;"
    "PWD=Rms_2024@#$;"
    "TDS_Version=7.4;"
    "Port=1433;"
)

# Alternative: Use ODBC Driver 17 if you have it installed
# DATABASE_URL = (
#     "Driver={ODBC Driver 17 for SQL Server};"
#     "Server=52.172.139.167;"
#     "Database=SiteSurveillance;"
#     "Uid=Rms;"
#     "Pwd=Rms_2024@#$;"
# )

 
async def test_connection():
    if not DATABASE_URL:
        print("Error: DATABASE_URL is not set.")
        return

    conn_str = DATABASE_URL
    print(f"Connecting to: {conn_str}")

    try:
        conn = await aioodbc.connect(dsn=conn_str)  # add autocommit=True if you like
        async with conn.cursor() as cur:
            await cur.execute("SELECT @@VERSION")
            row = await cur.fetchone()
            print("Connection Successful!")
            print(f"SQL Server Version: {row[0]}")
        
        await conn.close()
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())