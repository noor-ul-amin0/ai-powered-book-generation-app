from fastapi import FastAPI

app = FastAPI()

# Serve the frontend files from the dist directory
app.frontend(path='/', directory='dist', fallback='index.html')

# Rest of the API routes
@app.get("/test")
def read_root():
    return {"Hello": "World"}
