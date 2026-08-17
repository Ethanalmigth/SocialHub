import asyncio
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exception import CustomException
from model import Publication
from repository.post import PostRepository
from repository.publication import PublicationRepository
from repository.reseaux import ReseauxRepository
from repository.user import UserRepository
from schema import publication
from schema.publication import PublicationCreate, PublicationResponse


class PublicationService:
    def __init__(self,db:AsyncSession):
        self.repo = PublicationRepository(db)
        self.db = db
        self.repo_post=PostRepository(db)
        self.repo_reseaux= ReseauxRepository(db)
        self.repo_user=UserRepository(db)

    async def create(self,publication: PublicationCreate,user_id):
        post= await self.repo_post.get_post_by_id(publication.post_id)
        reseaux=await self.repo_reseaux.get_reseaux_by_id(publication.reseaux_id)
        if not post:
            raise CustomException(status_code=400,message="Post not found")
        if str(post.user_id) != str(user_id):
            raise CustomException(status_code=400,message="Not authorized ")
        if not reseaux:
            raise CustomException(status_code=400,message="Reseaux not found")

        try:
          new_publication= await self.repo.create_publication(publication)
          await self.db.commit()
          await self.db.refresh(new_publication)
          return PublicationResponse(id=new_publication.id,
                                     reseaux_id=new_publication.reseaux_id,
                                     published_at=new_publication.published_at,
                                     status=new_publication.status,
                                     post_id=new_publication.post_id,
                                     scheduled_at=new_publication.schedule_at,
                                     created_at=new_publication.created_at
                                     )
        except Exception as e:
            await self.db.rollback()
            raise CustomException(status_code=400,message=f"Error creating publication {str(e)}")
        except IntegrityError as e:
            await self.db.rollback()
            if "uq_post_reseau" in str(e.orig):
                raise CustomException(
                    status_code=409,
                    message=f"This post is already scheduled/published on this network."
                )
            raise CustomException(status_code=400, message="Could not create publication")

    async def get_publications_by_post(
            self,
            user_id: UUID,
            post_id: UUID
    ) -> list[PublicationResponse]:
        post = await self.repo_post.get_post_by_id(post_id)

        if not post:
            raise CustomException(
                status_code=404,
                message="Post not found"
            )

        if str(post.user_id) != str(user_id):
            raise CustomException(
                status_code=403,
                message="Not authorized to access this post"
            )

        publications = await self.repo.get_all_publications_by_post(post_id)

        return [PublicationResponse(
            id=pub.id,
            reseaux_id=pub.reseaux_id,
            published_at=pub.published_at,
            status=pub.status,
            post_id=pub.post_id,
            scheduled_at=pub.schedule_at,
            created_at=pub.created_at
        ) for pub in publications]