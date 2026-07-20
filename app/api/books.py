from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.config import get_session
from app.models import Book, BookStatus
from app.repositories import BookRepository, BookChapterRepository
from app.services import BookGenerationService
from app.schemas import (
    BookCreate,
    BookResponse,
    BookDetailResponse,
    SSEEvent
)
from app.storage import get_storage

router = APIRouter(prefix="/api/books", tags=["books"])


@router.post("", response_model=BookResponse)
async def create_book(
    book_data: BookCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
):
    repo = BookRepository(session)
    book = await repo.create({
        "title": book_data.title,
        "status": BookStatus.PENDING
    })
    return book


@router.get("", response_model=List[BookResponse])
async def list_books(session: AsyncSession = Depends(get_session)):
    repo = BookRepository(session)
    return await repo.get_all_not_archived()


@router.get("/{book_id}", response_model=BookDetailResponse)
async def get_book(book_id: int, session: AsyncSession = Depends(get_session)):
    repo = BookRepository(session)
    book = await repo.get_with_chapters(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.get("/{book_id}/stream")
async def stream_book_generation(book_id: int, session: AsyncSession = Depends(get_session)):
    service = BookGenerationService(session)

    async def event_generator():
        async for event in service.generate_book(book_id):
            yield f"event: {event.event}\ndata: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/{book_id}/download")
async def download_book(book_id: int, session: AsyncSession = Depends(get_session)):
    repo = BookRepository(session)
    book = await repo.get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not book.pdf_path:
        raise HTTPException(status_code=400, detail="PDF not available yet")

    return FileResponse(
        path=book.pdf_path,
        filename=f"{book.title.replace(' ', '_')}.pdf",
        media_type="application/pdf"
    )


@router.delete("/{book_id}")
async def delete_book(book_id: int, session: AsyncSession = Depends(get_session)):
    repo = BookRepository(session)
    book = await repo.get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Delete PDF
    if book.pdf_path:
        import os
        try:
            os.unlink(book.pdf_path)
        except:
            pass

    # Delete from DB
    await repo.delete(book_id)
    return {"message": "Book deleted successfully"}
