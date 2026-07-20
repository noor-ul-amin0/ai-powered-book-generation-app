import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from app.models import Book, BookChapter


class PDFService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12
        )
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            spaceAfter=6
        )

    async def generate_pdf(self, book: Book, chapters: list[BookChapter]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        story = []

        # Cover page
        story.append(Spacer(1, 3 * inch))
        story.append(Paragraph(book.title, self.title_style))
        story.append(PageBreak())

        # Table of contents
        story.append(Paragraph("Table of Contents", self.heading_style))
        story.append(Spacer(1, 12))
        for chapter in chapters:
            toc_line = f"Chapter {chapter.chapter_number}: {chapter.title}"
            story.append(Paragraph(toc_line, self.body_style))
        story.append(PageBreak())

        # Chapters
        for chapter in chapters:
            story.append(Paragraph(f"Chapter {chapter.chapter_number}: {chapter.title}", self.heading_style))
            story.append(Spacer(1, 12))
            if chapter.content:
                # Split content into paragraphs
                for para in chapter.content.split("\n\n"):
                    if para.strip():
                        story.append(Paragraph(para.strip(), self.body_style))
            story.append(PageBreak())

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
