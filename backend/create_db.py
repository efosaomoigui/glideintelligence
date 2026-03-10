import asyncio
import asyncpg
import sys

async def create_db():
    try:
        # Connect to the default 'postgres' database to create the new database
        conn = await asyncpg.connect(
            user='postgres', 
            password='mysecure123', 
            database='postgres', 
            host='localhost'
        )
        try:
            await conn.execute('CREATE DATABASE news_intelligence')
            print("Database news_intelligence created successfully.")
        except asyncpg.exceptions.DuplicateDatabaseError:
            print("Database news_intelligence already exists.")
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"Error creating database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(create_db())
