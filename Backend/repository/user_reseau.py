import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from model.reseaux import Reseaux
from model.user_reseau import UserReseau


class UserReseauRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def insert(
        self,
        user_id: uuid.UUID,
        reseaux_id: int,
        external_user_id: str,
        author_urn: str,
        access_token: str,
        expires_at: datetime,
        refresh_token: str | None = None,
    ) -> UserReseau:
        entry = UserReseau(
            user_id=user_id,
            reseaux_id=reseaux_id,
            external_user_id=external_user_id,
            author_urn=author_urn,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def get_connected_reseaux_names(self, user_id: uuid.UUID) -> list[str]:
        """Retourne les noms des réseaux auxquels l'utilisateur est connecté."""
        result = await self.db.execute(
            select(Reseaux.name)
            .join(UserReseau, UserReseau.reseaux_id == Reseaux.id)
            .where(UserReseau.user_id == user_id)
        )
        return [row[0] for row in result.all()]

    async def get_by_user_and_reseau(
        self, user_id: uuid.UUID, reseaux_id: int
    ) -> UserReseau | None:
        result = await self.db.execute(
            select(UserReseau).where(
                UserReseau.user_id == user_id,
                UserReseau.reseaux_id == reseaux_id,
            )
        )
        return result.scalar_one_or_none()

    async def update(self, entry: UserReseau, **kwargs) -> UserReseau:
        for key, value in kwargs.items():
            setattr(entry, key, value)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def upsert(
        self,
        user_id: uuid.UUID,
        reseaux_id: int,
        external_user_id: str,
        author_urn: str,
        access_token: str,
        expires_at: datetime,
        refresh_token: str | None = None,
    ) -> UserReseau:
        existing = await self.get_by_user_and_reseau(user_id, reseaux_id)
        if existing:
            return await self.update(
                existing,
                external_user_id=external_user_id,
                author_urn=author_urn,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )
        return await self.insert(
            user_id=user_id,
            reseaux_id=reseaux_id,
            external_user_id=external_user_id,
            author_urn=author_urn,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )



    async def delete(self, entry: UserReseau) -> None:
        await self.db.delete(entry)
        await self.db.commit()