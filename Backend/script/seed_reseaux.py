# scripts/seed_reseaux.py
import asyncio
from core.engine import SessionLocal
from model import Reseaux

RESEAUX_DATA = [
    {"name": "twitter", "max_characters": 280, "api_base_url": "https://api.twitter.com/2"},
    {"name": "linkedin", "max_characters": 3000, "api_base_url": "https://api.linkedin.com/v2"},
    {"name": "instagram", "max_characters": 2200, "api_base_url": "https://graph.instagram.com"},
]

async def seed():
    async with SessionLocal() as db:
        for data in RESEAUX_DATA:
            reseaux = Reseaux(**data)
            db.add(reseaux)
        await db.commit()
    print(f"{len(RESEAUX_DATA)} réseaux ajoutés.")

if __name__ == "__main__":
    asyncio.run(seed())