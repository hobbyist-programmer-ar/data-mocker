from fastapi import FastAPI
from app.api.router import router as api_router

app = FastAPI(title="Data Mocker API")

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
