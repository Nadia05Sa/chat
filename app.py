import threading
import asyncio
from flask import Flask
from ws_server import iniciar_ws
from config import oauth
from index import rutas
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev_secret")

oauth.init_app(app)
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration"
)

app.register_blueprint(rutas)

@app.get("/")
def home():
    return {"mensaje": "Flask y WebSocket funcionando"}

def lanzar_ws():
    asyncio.run(iniciar_ws())

if __name__ == "__main__":
    hilo = threading.Thread(target=lanzar_ws, daemon=True)
    hilo.start()

    print("Iniciando Flask…")
    app.run(debug=True, port=5000, use_reloader=False)
