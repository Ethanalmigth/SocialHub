from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from repository.refreshToken import RefreshTokenRepository


class RefreshTokenService:
    def __init__(self, db: AsyncSession):
        self.repo = RefreshTokenRepository(db)

    async def register(self, token: str, user_id: str, expires_at: datetime):
        await self.repo.register_refresh_token(token, user_id, expires_at)

    async def get_refresh_token(self, refresh_token:str):
        token =await self.repo.get_refresh_token_by_token(refresh_token)
        if token and not token.revoked:
            await self.repo.delete_refresh_token(refresh_token)
            return True
        return False
