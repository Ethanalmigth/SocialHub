from sqlalchemy import select

from model import Reseaux


class ReseauxRepository:
     def __init__(self,db) -> None:
         self.db = db

     async def get_reseaux_by_id(self,id:int):
         reseaux= await self.db.execute(select(Reseaux).where(Reseaux.id == id))
         return reseaux.scalar_one_or_none()