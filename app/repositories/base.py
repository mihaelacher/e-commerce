from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository[ModelType: Base]:
    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: int) -> ModelType | None:
        stmt = select(self.model).where(self.model.id == id)

        return self.db.scalar(stmt)

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)

        return list(self.db.scalars(stmt).all())

    def add(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)

        return obj

    def update(
        self,
        obj: ModelType,
        data: dict,
    ) -> ModelType:
        for key, value in data.items():
            setattr(obj, key, value)

        self.db.flush()
        self.db.refresh(obj)

        return obj

    def delete(self, obj: ModelType) -> None:
        self.db.delete(obj)
