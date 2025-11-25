import asyncio
import aioodbc
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def test_connection():
    if not DATABASE_URL:
        print("Error: DATABASE_URL is not set.")
        return

    print(f"Connecting to: {DATABASE_URL}")
    try:
        # Check if it's a valid ODBC string or needs conversion (logic from main.py)
        conn_str = DATABASE_URL
        if ";" not in conn_str or "Driver=" not in conn_str:
             print("Warning: DATABASE_URL does not look like an ODBC connection string.")
        
        conn = await aioodbc.connect(dsn=conn_str)
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
