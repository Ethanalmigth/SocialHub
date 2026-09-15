# services/linkedin_publisher.py
import logging
import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response, JSONResponse

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
    USERINFO_URL = "https://api.linkedin.com/v2/userinfo"  #

    def __init__(self, user_reseau: UserReseau, db: AsyncSession):
        self.user_reseau = user_reseau
        self.db = db

    # ------------------------------------------------------------------ #
    # OAuth
    # ------------------------------------------------------------------ #

    async def auth(self, payload=Depends(controle_access_token)):
        state = secrets.token_urlsafe(32)
        user_id = str(payload.get("id"))

        data = {
            "response_type": "code",
            "redirect_uri": settings.REDIRECT_URL,
            "client_id": settings.CLIENT_ID,
            "state": state,
            "scope": "openid profile w_member_social",
        }
        url = f"{self.AUTHORIZATION_URL}?{urllib.parse.urlencode(data)}"

        # JSON, pas RedirectResponse : le frontend fait window.location.href lui-même
        reponse = JSONResponse(content={"authorization_url": url})
        reponse.set_cookie(
            key=STATE_COOKIE_KEY,
            value=state,
            max_age=300,
            httponly=True,
            samesite="lax",
            secure=False,
        )
        reponse.set_cookie(
            key=USER_COOKIE_KEY,
            value=user_id,
            max_age=300,
            httponly=True,
            samesite="lax",
            secure=False,
        )
        return reponse

    async def callback(
            self,
            request: Request,
            code: str = Query(...),
            state: str = Query(...),
            db=Depends(get_db),
    ):
        cookie_state = request.cookies.get(STATE_COOKIE_KEY)
        cookie_user_id = request.cookies.get(USER_COOKIE_KEY)

        logger.error("DEBUG callback: cookie_state=%r, param_state=%r, cookie_user_id=%r", cookie_state, state,
                     cookie_user_id)

        if not cookie_state or not secrets.compare_digest(state, cookie_state):
            logger.error("DEBUG callback: ECHEC sur state mismatch")
            return self._redirect_with_error("linkedin")
        if not cookie_user_id:
            logger.error("DEBUG callback: ECHEC cookie_user_id manquant")
            return self._redirect_with_error("linkedin")

        try:
            data_auth = await self._exchange_code_for_token(code)
            access_token = data_auth["access_token"]
            user_data = await self._fetch_user_info(access_token)
        except CustomException as exc:
            logger.error("DEBUG callback: ECHEC exchange/userinfo -> %s", exc)
            return self._redirect_with_error("linkedin")

        author_urn = f"urn:li:person:{user_data['sub']}"
        expires_in = data_auth.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        reseaux_repo = ReseauxRepository(db)
        reseau_linkedin = await reseaux_repo.get_by_name("linkedin")
        if not reseau_linkedin:
            logger.error("DEBUG callback: ECHEC reseau_linkedin introuvable en base")
            return self._redirect_with_error("linkedin")

        logger.error("DEBUG callback: succès jusqu'ici, upsert en cours...")

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

        logger.error("DEBUG callback: upsert OK, redirection succès")

        redirect = RedirectResponse(url=f"http://localhost:5173/auth?connected=linkedin")
        redirect.delete_cookie(key=STATE_COOKIE_KEY)
        redirect.delete_cookie(key=USER_COOKIE_KEY)
        return redirect

    @staticmethod
    def _redirect_with_error(platform: str) -> RedirectResponse:
        response = RedirectResponse(url=f"http://localhost:5173/auth?error={platform}")
        response.delete_cookie(key=STATE_COOKIE_KEY)
        response.delete_cookie(key=USER_COOKIE_KEY)
        return response

    async def _exchange_code_for_token(self, code: str) -> dict:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "redirect_uri": settings.REDIRECT_URL,
        }
        logger.error(
            "DEBUG exchange: client_id=%r, secret_len=%d, secret_start=%r, redirect_uri=%r",
            data["client_id"],
            len(data["client_secret"]) if data["client_secret"] else 0,
            data["client_secret"][:4] if data["client_secret"] else None,
            data["redirect_uri"],
        )
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
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
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