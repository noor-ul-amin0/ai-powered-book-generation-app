from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class BookStatus(str, Enum):
    PENDING = "PENDING"
    GENERATING_OUTLINE = "GENERATING_OUTLINE"
    GENERATING_CHAPTERS = "GENERATING_CHAPTERS"
    GENERATING_PDF = "GENERATING_PDF"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ChapterGenerationStatus(str, Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Book(SQLModel, table=True):
    __tablename__ = "books"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    outline: Optional[str] = Field(default=None)
    status: BookStatus = Field(default=BookStatus.PENDING, index=True)
    total_chapters: Optional[int] = Field(default=None)
    generated_chapters: int = Field(default=0)
    pdf_path: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    retry_count: int = Field(default=0)
    is_archived: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    chapters: List["BookChapter"] = Relationship(
        back_populates="book",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class BookChapter(SQLModel, table=True):
    __tablename__ = "book_chapters"

    id: Optional[int] = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key="books.id", index=True)
    chapter_number: int = Field(index=True)
    title: str
    content: Optional[str] = Field(default=None)
    generation_status: ChapterGenerationStatus = Field(default=ChapterGenerationStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    book: Book = Relationship(back_populates="chapters")
