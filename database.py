import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "TalkLib")

client = None
db = None

async def connect_db():
    global client, db
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    print(f"✅ Conectado ao MongoDB: {DATABASE_NAME}")
    return db

def get_db():
    return db
