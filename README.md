# AI Book Generator

An AI-powered application for generating books with structured outlines, chapters, and professional PDFs using FastAPI, React, and LiteLLM.

## Features

- 📚 Generate book outlines from a title
- ✍️ Write chapters sequentially using AI
- 📄 Create professional PDF documents
- 🔄 Real-time progress streaming with SSE
- 💾 Persist books and chapters in PostgreSQL
- 📦 Docker support for easy deployment
- 🤖 Support for multiple LLM providers (Groq, OpenAI, Anthropic, etc.)

## Tech Stack

**Backend:**
- FastAPI
- SQLModel (async PostgreSQL)
- LiteLLM
- ReportLab
- Python 3.13+

**Frontend:**
- React
- Tailwind CSS
- Vite
- Lucide Icons

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js & npm
- PostgreSQL (or use Docker)
- API key for your preferred LLM provider (e.g., Groq)

### Local Development

1. **Clone the repository**

2. **Create a .env file**
   ```bash
   cp .env.example .env
   ```

3. **Update .env with your configuration**
   - Set `LLM_API_KEY` to your actual API key
   - Configure `DATABASE_URL` if not using Docker

4. **Install backend dependencies**
   ```bash
   uv sync
   ```

5. **Run PostgreSQL (or use Docker)**
   ```bash
   docker-compose up -d db
   ```

6. **Start the application**
   ```bash
   uv run fastapi dev main.py
   ```

7. **Visit the app** at http://localhost:8000

### Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## API Endpoints

- `POST /api/books` - Create a new book
- `GET /api/books` - List all books
- `GET /api/books/{id}` - Get book details with chapters
- `GET /api/books/{id}/stream` - Stream generation progress (SSE)
- `GET /api/books/{id}/download` - Download generated PDF
- `DELETE /api/books/{id}` - Delete a book

## Project Structure

```
book-generator-and-downloader/
├── app/
│   ├── api/              # API routes
│   ├── services/         # Business logic
│   ├── repositories/     # Database access
│   ├── models/           # SQLModel models
│   ├── schemas/          # Pydantic schemas
│   ├── prompts/          # LLM prompt templates
│   ├── storage/          # Storage providers
│   ├── config/           # Settings & DB config
│   └── logging/          # Logging setup
├── frontend/             # React application
├── dist/                 # Frontend build output
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## License

MIT
