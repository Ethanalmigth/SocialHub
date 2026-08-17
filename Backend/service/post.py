from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.exception import CustomException
from repository.post import PostRepository
from schema.post import PostCreate, PostResponse

class PostService:
    def __init__(self,db:AsyncSession):
        self.repo=PostRepository(db)
        self.db=db

    async def create(self,post:PostCreate,user_id:UUID):
        try:
            new_post = await self.repo.create(post,user_id)
            await self.db.commit()
            await self.db.refresh(new_post)
            return PostResponse(id=new_post.id,user_id=user_id,title=new_post.title,content=new_post.content,created_at=new_post.created_at,updated_at=new_post.updated_at)
        except Exception as e:
            await self.db.rollback()
            raise CustomException(status_code=400,message=str(e))

    async def get_all_posts(self,user_id:UUID):
        try:
            results = await self.repo.get_all_posts(user_id)
            return [PostResponse(id=post.id,user_id=post.user_id,title=post.title,content=post.content,created_at=post.created_at,updated_at=post.updated_at) for post in results]
        except Exception as e:
            raise CustomException(status_code=400,message=str(e))

    async def delete_post(self,post_id:UUID,user_id:UUID):
        post = await self.repo.get_post_by_id(post_id)
        if not post:
            raise CustomException(status_code=404, message=f"Post with id {post_id} not found")
        if str(post.user_id) != str (user_id):
            print(post.user_id)
            raise CustomException(status_code=403, message=f"Not allowed to delete post with id: {post_id}")
        try:
           await self.repo.delete_post(post_id)
           await self.db.commit()
           return PostResponse(id=post.id,user_id=post.user_id,title=post.title,content=post.content,created_at=post.created_at,updated_at=post.updated_at)
        except Exception as e:
            await self.db.rollback()
            raise CustomException(status_code=400, message=f"Something went wrong while deleting post {post_id}: {e}")
