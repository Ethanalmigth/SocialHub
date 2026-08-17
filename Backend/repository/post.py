from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from model import Post
from schema.post import PostCreate


class PostRepository:
    def __init__(self,db:AsyncSession):
        self.db = db

    async def create(self,post:PostCreate,user_id:UUID):
        new_post = Post(title=post.title,content=post.content,user_id=user_id)
        self.db.add(new_post)
        return new_post

    async def get_all_posts(self,user_id:UUID):
        result=await self.db.execute(select(Post).where(Post.user_id == user_id))
        return result.scalars().all()

    async def get_post_by_id(self,post_id:UUID):
        result=await self.db.execute(select(Post).where(Post.id == post_id))
        return result.scalar_one_or_none()

    async def delete_post(self,post_id:UUID):
        await self.db.execute(delete(Post).where(Post.id == post_id))
