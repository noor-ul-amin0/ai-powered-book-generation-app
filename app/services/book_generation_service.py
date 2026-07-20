import json
import io
from typing import AsyncGenerator
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Book, BookChapter, BookStatus, ChapterGenerationStatus
from app.repositories import BookRepository, BookChapterRepository
from app.services import LLMService, PDFService
from app.storage import get_storage
from app.prompts import SYSTEM_PROMPT_OUTLINE, SYSTEM_PROMPT_CHAPTER
from app.schemas import SSEEvent


class BookGenerationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.book_repo = BookRepository(session)
        self.chapter_repo = BookChapterRepository(session)
        self.llm_service = LLMService()
        self.pdf_service = PDFService()
        self.storage = get_storage()

    async def generate_book(self, book_id: int) -> AsyncGenerator[SSEEvent, None]:
        book = await self.book_repo.get(book_id)
        if not book:
            yield SSEEvent(event="error", data={"message": "Book not found"})
            return

        try:
            # Step 1: Generate outline
            if not book.outline:
                yield SSEEvent(event="generation_started", data={"book_id": book_id})
                yield SSEEvent(event="outline_started", data={"book_id": book_id})

                outline_json_str = await self.llm_service.generate(
                    SYSTEM_PROMPT_OUTLINE,
                    f"Generate an outline for a book titled: {book.title}"
                )
                outline_data = json.loads(outline_json_str)

                book = await self.book_repo.update(book, {
                    "outline": outline_json_str,
                    "status": BookStatus.GENERATING_OUTLINE,
                    "total_chapters": len(outline_data["chapters"])
                })
                yield SSEEvent(event="outline_created", data={"book_id": book_id, "outline": outline_data})

                # Create chapter records
                for chapter in outline_data["chapters"]:
                    await self.chapter_repo.create({
                        "book_id": book_id,
                        "chapter_number": chapter["chapter_number"],
                        "title": chapter["title"],
                        "generation_status": ChapterGenerationStatus.PENDING
                    })

                book = await self.book_repo.update(book, {
                    "status": BookStatus.GENERATING_CHAPTERS
                })

            # Step 2: Generate chapters
            chapters = await self.chapter_repo.get_all_by_book_id(book_id)
            outline_data = json.loads(book.outline) if book.outline else {}

            for chapter in chapters:
                if chapter.generation_status == ChapterGenerationStatus.COMPLETED:
                    continue

                yield SSEEvent(event="chapter_started", data={
                    "book_id": book_id,
                    "chapter_number": chapter.chapter_number,
                    "title": chapter.title
                })

                chapter = await self.chapter_repo.update(chapter, {
                    "generation_status": ChapterGenerationStatus.GENERATING
                })

                # Prepare context from previous chapters
                previous_chapters_content = ""
                for prev_chapter in chapters:
                    if prev_chapter.chapter_number < chapter.chapter_number and prev_chapter.content:
                        previous_chapters_content += f"\n\nChapter {prev_chapter.chapter_number}: {prev_chapter.title}\n{prev_chapter.content}"

                chapter_content = await self.llm_service.generate(
                    SYSTEM_PROMPT_CHAPTER,
                    f"""Book title: {book.title}
                    Outline: {json.dumps(outline_data, indent=2)}
                    Current chapter: Chapter {chapter.chapter_number} - {chapter.title}
                    Previous chapters: {previous_chapters_content}

                    Write the content for this chapter."""
                )

                chapter = await self.chapter_repo.update(chapter, {
                    "content": chapter_content,
                    "generation_status": ChapterGenerationStatus.COMPLETED
                })

                book = await self.book_repo.update(book, {
                    "generated_chapters": book.generated_chapters + 1,
                    "updated_at": datetime.utcnow()
                })

                yield SSEEvent(event="chapter_completed", data={
                    "book_id": book_id,
                    "chapter_number": chapter.chapter_number,
                    "title": chapter.title,
                    "content": chapter_content
                })

            # Step 3: Generate PDF
            yield SSEEvent(event="pdf_generation_started", data={"book_id": book_id})
            book = await self.book_repo.update(book, {"status": BookStatus.GENERATING_PDF})

            chapters = await self.chapter_repo.get_all_by_book_id(book_id)
            pdf_bytes = await self.pdf_service.generate_pdf(book, chapters)

            # Save PDF
            from pathlib import Path
            storage_path = Path(self.storage.base_path) / "books" / str(book_id)
            storage_path.mkdir(parents=True, exist_ok=True)
            pdf_file_path = storage_path / "book.pdf"
            with open(pdf_file_path, "wb") as f:
                f.write(pdf_bytes)

            book = await self.book_repo.update(book, {
                "pdf_path": str(pdf_file_path),
                "status": BookStatus.COMPLETED,
                "updated_at": datetime.utcnow()
            })

            yield SSEEvent(event="completed", data={"book_id": book_id, "pdf_path": str(pdf_file_path)})

        except Exception as e:
            book = await self.book_repo.get(book_id)
            if book:
                await self.book_repo.update(book, {
                    "status": BookStatus.FAILED,
                    "error_message": str(e)
                })
            yield SSEEvent(event="failed", data={"book_id": book_id, "error": str(e)})
