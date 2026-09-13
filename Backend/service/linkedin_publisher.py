# services/linkedin_publisher.py
import logging
import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from core.engine import get_db
from core.exception import CustomException
from core.setting import settings
from model.user_reseau import UserReseau
from repository.reseaux import ReseauxRepository
from repository.user_reseau import UserReseauRepository
from schema.ReponseAPI import ReponseAPI
from utils.token import controle_access_token

logger = logging.getLogger(__name__)

STATE_COOKIE_KEY = "state"
USER_COOKIE_KEY = "oauth_user_id"

# Timeout explicite pour tous les appels sortants vers LinkedIn
HTTP_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


class LinkedInPublisher:
    UGC_POSTS_URL = "https://api.linkedin.com/v2/ugcPosts"
    AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    USERINFO_URL = "https://www.linkedin.com/v2/userinfo"

    def __init__(self, user_reseau: UserReseau, db: AsyncSession):
        self.user_reseau = user_reseau
        self.db = db

    # ------------------------------------------------------------------ #
    # OAuth
    # ------------------------------------------------------------------ #

    async def auth(self, payload=Depends(controle_access_token)):
        state = secrets.token_urlsafe(32)
        user_id = str(payload.get("sub"))

        data = {
            "response_type": "code",
            "redirect_uri": settings.redirect_url,
            "client_id": settings.client_id,
            "state": state,
            "scope": "w_member_social",
        }
        url = f"{self.AUTHORIZATION_URL}?{urllib.parse.urlencode(data)}"

        reponse = RedirectResponse(url=url)
        reponse.set_cookie(
            key=STATE_COOKIE_KEY,
            value=state,
            max_age=300,
            httponly=True,
            samesite="lax",
            secure=True,
        )
        reponse.set_cookie(
            key=USER_COOKIE_KEY,
            value=user_id,
            max_age=300,
            httponly=True,
            samesite="lax",
            secure=True,
        )
        return reponse

    async def callback(
        self,
        request: Request,
        response: Response,
        code: str = Query(...),
        state: str = Query(...),
        db=Depends(get_db),
    ):
        cookie_state = request.cookies.get(STATE_COOKIE_KEY)
        cookie_user_id = request.cookies.get(USER_COOKIE_KEY)

        if not cookie_state or not secrets.compare_digest(state, cookie_state):
            raise CustomException(status_code=401, message="State invalide (CSRF suspecté)")
        if not cookie_user_id:
            raise CustomException(status_code=401, message="Session utilisateur introuvable")

        data_auth = await self._exchange_code_for_token(code)
        access_token = data_auth["access_token"]
        user_data = await self._fetch_user_info(access_token)
        author_urn = f"urn:li:person:{user_data['sub']}"

        expires_in = data_auth.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        reseaux_repo = ReseauxRepository(db)
        reseau_linkedin = await reseaux_repo.get_by_name("linkedin")
        if not reseau_linkedin:
            raise CustomException(status_code=500, message="Réseau 'linkedin' non configuré en base")

        repo = UserReseauRepository(db)
        await repo.upsert(
            user_id=cookie_user_id,
            reseaux_id=reseau_linkedin.id,
            external_user_id=user_data["sub"],
            author_urn=author_urn,
            access_token=access_token,
            refresh_token=data_auth.get("refresh_token"),
            expires_at=expires_at,
        )

        response.delete_cookie(key=STATE_COOKIE_KEY)
        response.delete_cookie(key=USER_COOKIE_KEY)

        return ReponseAPI(
            success=True,
            message="Authorisation linkedin confirmer",
            data={"author_urn": author_urn, "user": user_data},
        )

    async def _exchange_code_for_token(self, code: str) -> dict:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
            "redirect_uri": settings.redirect_url,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                token_response = await client.post(self.TOKEN_URL, data=data, headers=headers)
        except httpx.HTTPError as exc:
            logger.exception("Erreur réseau lors de l'échange du code LinkedIn")
            raise CustomException(status_code=502, message="Impossible de contacter LinkedIn") from exc

        if token_response.status_code != 200:
            logger.error("Erreur token LinkedIn: %s", token_response.text)
            raise CustomException(status_code=token_response.status_code, message="Erreur d'authentification LinkedIn")

        return token_response.json()

    async def _fetch_user_info(self, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                user_response = await client.get(self.USERINFO_URL, headers=headers)
        except httpx.HTTPError as exc:
            logger.exception("Erreur réseau lors de la récupération du profil LinkedIn")
            raise CustomException(status_code=502, message="Impossible de contacter LinkedIn") from exc

        if user_response.status_code != 200:
            logger.error("Erreur userinfo LinkedIn: %s", user_response.text)
            raise CustomException(status_code=user_response.status_code, message="Impossible de récupérer le profil LinkedIn")

        return user_response.json()

    # ------------------------------------------------------------------ #
    # Publication
    # ------------------------------------------------------------------ #

    async def _ensure_valid_token(self) -> str:
        """Retourne un access_token valide, en le rafraîchissant si besoin."""
        expires_at = self.user_reseau.expires_at
        if expires_at and expires_at <= datetime.now(timezone.utc):
            if not self.user_reseau.refresh_token:
                raise CustomException(
                    status_code=401,
                    message="Token LinkedIn expiré et aucun refresh_token disponible, ré-authentification requise",
                )
            await self._refresh_access_token()

        return self.user_reseau.access_token

    async def _refresh_access_token(self) -> None:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.user_reseau.refresh_token,
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                token_response = await client.post(self.TOKEN_URL, data=data, headers=headers)
        except httpx.HTTPError as exc:
            logger.exception("Erreur réseau lors du refresh du token LinkedIn")
            raise CustomException(status_code=502, message="Impossible de contacter LinkedIn") from exc

        if token_response.status_code != 200:
            logger.error("Erreur refresh token LinkedIn: %s", token_response.text)
            raise CustomException(status_code=401, message="Impossible de rafraîchir le token LinkedIn, ré-authentification requise")

        data_auth = token_response.json()
        expires_in = data_auth.get("expires_in", 3600)

        self.user_reseau.access_token = data_auth["access_token"]
        self.user_reseau.refresh_token = data_auth.get("refresh_token", self.user_reseau.refresh_token)
        self.user_reseau.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        repo = UserReseauRepository(self.db)
        await repo.upsert(
            user_id=self.user_reseau.user_id,
            reseaux_id=self.user_reseau.reseaux_id,
            external_user_id=self.user_reseau.external_user_id,
            author_urn=self.user_reseau.author_urn,
            access_token=self.user_reseau.access_token,
            refresh_token=self.user_reseau.refresh_token,
            expires_at=self.user_reseau.expires_at,
        )

    async def publish(self, content: str) -> str:
        """Publie un post texte sur LinkedIn et retourne l'ID du post créé."""

        access_token = await self._ensure_valid_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        body = {
            "author": self.user_reseau.author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.post(self.UGC_POSTS_URL, json=body, headers=headers)
        except httpx.HTTPError as exc:
            logger.exception("Erreur réseau lors de la publication LinkedIn")
            raise CustomException(status_code=502, message="Impossible de contacter LinkedIn") from exc

        if response.status_code not in (200, 201):
            logger.error("Erreur publication LinkedIn: %s", response.text)
            raise CustomException(status_code=response.status_code, message="Erreur lors de la publication LinkedIn")

        # LinkedIn renvoie l'ID du post créé dans le header 'x-restli-id'
        linkedin_post_id = response.headers.get("x-restli-id")
        return linkedin_post_id