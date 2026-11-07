from typing import TYPE_CHECKING

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.enums.knowledge_document import KnowledgeDocumentType

if TYPE_CHECKING:
    from app.models.knowledge_chunk import KnowledgeChunkModel


class KnowledgeDocumentModel(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    document_type: Mapped[KnowledgeDocumentType] = mapped_column(
        Enum(
            KnowledgeDocumentType,
            name="knowledge_document_type",
        ),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    chunks: Mapped[list["KnowledgeChunkModel"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
