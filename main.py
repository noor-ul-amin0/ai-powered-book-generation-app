from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.config import create_db_and_tables
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

# Include API routes
app.include_router(api_router)

# Serve the frontend files from the dist directory
dist_path = Path("dist")
if dist_path.exists():
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")

# Test route
@app.get("/test")
def read_root():
    return {"Hello": "World"}

