from model.refreshtoken import RefreshToken

from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


class RefreshTokenRepository:
    def __init__(self, db:AsyncSession):
        self.db = db
    async def register_refresh_token(self,token:str, user_id:str, date: datetime) :
        refresh=RefreshToken(token=token,user_id=user_id,expire_at=date)
        self.db.add(refresh)
        await self.db.commit()
        await self.db.refresh(refresh)
        return refresh
    async def get_refresh_token_by_token(self,token:str) :
        refresh=await self.db.execute(select(RefreshToken).where(RefreshToken.token==token))
        return refresh.scalar_one_or_none()
    async def delete_refresh_token(self,token:str) :
        await self.db.execute(delete(RefreshToken).where(RefreshToken.token==token))
        await self.db.commit()
    async def delete_refresh_token_by_user_id(self,user_id:UUID) :
        await self.db.execute(delete(RefreshToken).where(RefreshToken.user_id==user_id))
        await self.db.commit()