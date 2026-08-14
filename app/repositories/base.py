from typing import Generic, Type, TypeVar
from sqlalchemy.orm import Session
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: int) -> ModelType | None:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        return self.db.query(self.model).offset(skip).limit(limit).all()

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
