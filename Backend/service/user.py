import traceback
from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from core.exception import CustomException
from core.setting import settings

from repository.refreshToken import RefreshTokenRepository
from repository.user import UserRepository
from schema.user import Userout, Userlogin, UserCreate
from utils.hash import verify_password
from utils.token import create_token, create_refresh_token, verify_token


class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)
        self.repoToken = RefreshTokenRepository(db)
        self.db = db

    async def _generate_and_save_tokens(self, user_id: UUID, email: str, name: str) -> tuple[str, str]:
        token_data = {"id": str(user_id), "email": email, "name": name}
        token = create_token(token_data)
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRES)
        refresh_token = create_refresh_token(token_data, expire)

        await self.repoToken.delete_refresh_token_by_user_id(user_id)
        await self.repoToken.register_refresh_token(refresh_token, user_id, expire)

        return token, refresh_token

    async def register_user(self, user: UserCreate) -> Userout:
        user_exist = await self.repo.get_user_by_email(user.email)
        if user_exist:
            raise CustomException( status_code=status.HTTP_409_CONFLICT,message="User already exist with this email" )
        try:
            user_created = await self.repo.create_user(user)
            token, refresh_token = await self._generate_and_save_tokens(  user_created.id, user_created.email, user_created.name)
            await self.db.commit()
            return Userout(id=str(user_created.id),email=user_created.email,name=user_created.name,token=token, refresh_token=refresh_token)
        except Exception as e:
            await self.db.rollback()
            traceback.print_exc()
            raise CustomException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=str(e))

    async def login_user(self, user: Userlogin) -> Userout:
        user_exist = await self.repo.get_user_by_email(user.email)
        if not user_exist:
            raise CustomException(status_code=status.HTTP_404_NOT_FOUND, message="User does not exist")

        if not verify_password(user.password, user_exist.hashed_password):
            raise CustomException(status_code=status.HTTP_401_UNAUTHORIZED, message="Incorrect Password")

        try:
            token, refresh_token = await self._generate_and_save_tokens(
                user_exist.id, user_exist.email, user_exist.name
            )
            await self.db.commit()
            return Userout(id=str(user_exist.id),email=user_exist.email,name=user_exist.name, token=token,refresh_token=refresh_token)
        except Exception as e:
            await self.db.rollback()
            raise CustomException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=str(e))

    async def refresh(self, refresh_token: str) -> Userout:
        try:
            payload = verify_token(refresh_token, "refresh")
            token_db = await self.repoToken.get_refresh_token_by_token(refresh_token)

            if not token_db:
                raise CustomException(status_code=status.HTTP_404_NOT_FOUND, message="No refresh token found")

            if token_db.revoked:
                await self.repoToken.delete_refresh_token(refresh_token)
                raise CustomException(status_code=status.HTTP_401_UNAUTHORIZED, message="Refresh Token revoke")

            if token_db.expire_at < datetime.now(timezone.utc):
                await self.repoToken.delete_refresh_token(refresh_token)
                raise CustomException(status_code=status.HTTP_401_UNAUTHORIZED, message="Token expired")

            token, refresh_token_new = await self._generate_and_save_tokens(
                payload["id"], payload["email"], payload["name"]
            )
            await self.db.commit()

            return Userout(id=str(payload["id"]), email=payload["email"], name=payload["name"], token=token, refresh_token=refresh_token_new)
        except CustomException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise CustomException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=str(e))

    async def logout(self, id_user: UUID) -> None:
        user = await self.repo.get_user_by_id(id_user)
        if not user:
            raise CustomException(status_code=status.HTTP_404_NOT_FOUND, message="User does not exist")

        try:
            await self.repoToken.delete_refresh_token_by_user_id(id_user)
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise CustomException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=str(e))