from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from enums.status_publication import StatusPublication
from model import Publication
from schema import publication
from schema.publication import PublicationCreate


class PublicationRepository():
    def __init__(self,db:AsyncSession):
        self.db = db

    async def create_publication(self,publication: PublicationCreate):
        new_publication= Publication(post_id=publication.post_id,reseaux_id=publication.reseaux_id,schedule_at=publication.schedule_at)
        self.db.add(new_publication)
        return new_publication

    async def get_all_publications_by_post(self,post_id):
        publications=await self.db.execute(select(Publication).where(Publication.post_id == post_id))
        return publications.scalars().all()

    async def get_all_publications_schedule_at(self, now: datetime):
        result = await self.db.execute(
            select(Publication)
            .options(
                selectinload(Publication.post),
                selectinload(Publication.reseaux),
            )
            .where(Publication.schedule_at <= now, Publication.status == StatusPublication.PENDING)
        )
        return result.scalars().all()

