from fastapi import FastAPI
from app.database import lifespan
from app.routers import auth

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)


@app.get("/", tags=["index"])
def home():
    return "Welcome to the research management api server"
