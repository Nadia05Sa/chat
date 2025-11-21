from fastapi import FastAPI
from db_manager import DatabaseManager
from config import MONGO_URI, DB_NAME

from routers.auth_router import router as auth_router
from routers.channels_router import router as channels_router
from routers.messages_router import router as messages_router
from websocket.ws_server import router as ws_router

db = DatabaseManager(MONGO_URI, DB_NAME)
db.conectar()

app = FastAPI()

app.include_router(auth_router)
app.include_router(channels_router)
app.include_router(messages_router)
app.include_router(ws_router)

@app.get("/")
def root():
    return {"ok": True, "msg": "Chat server funcionando"}
