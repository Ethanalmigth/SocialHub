from sqlalchemy import select

from model import Reseaux


class ReseauxRepository:
     def __init__(self,db) -> None:
         self.db = db

     async def get_reseaux_by_id(self,id:int):
         reseaux= await self.db.execute(select(Reseaux).where(Reseaux.id == id))
         return reseaux.scalar_one_or_none()


     async def get_all_reseaux(self):
         reseaux= await self.db.execute(select(Reseaux))
         reseaux=reseaux.scalars().all()
         reseaux=[{"id":i.id, "name":i.name}for i in reseaux]
         return reseaux

     async def get_by_name(self, name: str) -> Reseaux | None:
         result = await self.db.execute(select(Reseaux).where(Reseaux.name == name))
         return result.scalar_one_or_none()