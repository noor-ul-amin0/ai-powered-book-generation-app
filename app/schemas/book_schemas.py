from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models import BookStatus, ChapterGenerationStatus


class BookCreate(BaseModel):
    title: str


class BookResponse(BaseModel):
    id: int
    title: str
    outline: Optional[str]
    status: BookStatus
    total_chapters: Optional[int]
    generated_chapters: int
    pdf_path: Optional[str]
    error_message: Optional[str]
    retry_count: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookChapterResponse(BaseModel):
    id: int
    book_id: int
    chapter_number: int
    title: str
    content: Optional[str]
    generation_status: ChapterGenerationStatus
    created_at: datetime

    class Config:
        from_attributes = True


class BookDetailResponse(BookResponse):
    chapters: List[BookChapterResponse]


class SSEEvent(BaseModel):
    event: str
    data: dict
