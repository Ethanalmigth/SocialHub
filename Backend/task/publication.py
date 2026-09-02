# task/publication.py
import asyncio
from celery import shared_task

from core.engine import SessionLocal
from service.publication import PublicationService


@shared_task
def check_post():
   asyncio.run(_check_post())



async def _check_post():
    async with SessionLocal() as db:
        publication = PublicationService(db)
        await publication.publish_publication()