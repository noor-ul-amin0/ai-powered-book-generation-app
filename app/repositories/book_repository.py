from typing import List, Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.repositories.base import BaseRepository
from app.models import Book, BookChapter, BookStatus


class BookRepository(BaseRepository[Book]):
    def __init__(self, session: AsyncSession):
        super().__init__(Book, session)

    async def get_with_chapters(self, id: int) -> Optional[Book]:
        statement = select(Book).where(Book.id == id).options(selectinload(Book.chapters))
        results = await self.session.execute(statement)
        return results.scalar_one_or_none()

    async def get_all_not_archived(self) -> List[Book]:
        statement = select(Book).where(Book.is_archived == False)  # noqa: E712
        results = await self.session.execute(statement)
        return list(results.scalars().all())


class BookChapterRepository(BaseRepository[BookChapter]):
    def __init__(self, session: AsyncSession):
        super().__init__(BookChapter, session)

    async def get_by_book_and_number(self, book_id: int, chapter_number: int) -> Optional[BookChapter]:
        statement = select(BookChapter).where(
            BookChapter.book_id == book_id,
            BookChapter.chapter_number == chapter_number
        )
        results = await self.session.execute(statement)
        return results.scalar_one_or_none()

    async def get_all_by_book_id(self, book_id: int) -> List[BookChapter]:
        statement = select(BookChapter).where(BookChapter.book_id == book_id).order_by(BookChapter.chapter_number)
        results = await self.session.execute(statement)
        return list(results.scalars().all())
