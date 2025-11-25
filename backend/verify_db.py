import asyncio
import aioodbc


DATABASE_URL = ("Driver={ODBC Driver 17 for SQL Server};"
                "Server=52.172.139.167;"
                "Database=SiteSurveillance;"
                "Uid=Rms;"
                "Pwd={Rms_2024@#$};"
)
 
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