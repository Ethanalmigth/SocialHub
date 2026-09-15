from datetime import datetime, timezone
from uuid import UUID

from psycopg.transaction import BaseTransaction
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exception import CustomException
from enums.status_publication import StatusPublication
from model import Publication
from repository.post import PostRepository
from repository.publication import PublicationRepository
from repository.reseaux import ReseauxRepository
from repository.user import UserRepository
from schema import publication
from schema.publication import PublicationCreate, PublicationResponse


from repository.user_reseau import UserReseauRepository
from service.linkedin_publisher import LinkedInPublisher

import logging

logger = logging.getLogger(__name__)


class PublicationService:
    def __init__(self, db: AsyncSession):
        self.repo = PublicationRepository(db)
        self.db = db
        self.repo_post = PostRepository(db)
        self.repo_reseaux = ReseauxRepository(db)
        self.repo_user = UserRepository(db)
        self.repo_user_reseau = UserReseauRepository(db)

    async def create(self, publication: PublicationCreate, user_id: UUID):
        post = await self.repo_post.get_post_by_id(publication.post_id)
        if not post:
            raise CustomException(status_code=404, message="Post introuvable")

        if str(post.user_id) != str(user_id):
            raise CustomException(status_code=403, message="Accès non autorisé à ce post")

        new_publication = await self.repo.create_publication(publication)
        await self.db.commit()
        await self.db.refresh(new_publication)
        return new_publication

    async def get_publications_by_post(self, user_id: UUID, post_id: UUID):
        post = await self.repo_post.get_post_by_id(post_id)
        if not post:
            raise CustomException(status_code=404, message="Post introuvable")

        if str(post.user_id) != str(user_id):
            raise CustomException(status_code=403, message="Accès non autorisé à ce post")

        publications = await self.repo.get_all_publications_by_post(post_id)
        return publications




    async def publish_publication(self):
        now = datetime.now(timezone.utc)
        publications = await self.repo.get_all_publications_schedule_at(now)

        for pub in publications:
            await self._publish_single(pub, now)

    async def _publish_single(self, pub: Publication, now: datetime) -> None:
        try:
            user_reseau = await self.repo_user_reseau.get_by_user_and_reseau(
                user_id=pub.post.user_id,
                reseaux_id=pub.reseaux_id,
            )
            if not user_reseau:
                raise CustomException(status_code=400, message="Aucun compte connecté pour ce réseau")

            if user_reseau.expires_at < now:
                raise CustomException(status_code=401, message="Token expiré, reconnexion nécessaire")

            if len(pub.post.content) > pub.reseaux.max_characters:
                raise CustomException(status_code=400, message="Contenu trop long pour ce réseau")

            publisher = LinkedInPublisher(user_reseau, self.db)
            await publisher.publish(content=pub.post.content)

            pub.published_at = now
            pub.status = StatusPublication.PUBLISHED
            await self.db.commit()

        except Exception as e:
            logger.exception("Échec de publication pour pub_id=%s: %s", pub.id, e)
            await self.db.rollback()
            pub.status = StatusPublication.FAILED
            try:
                await self.db.commit()
            except Exception:
                await self.db.rollback()