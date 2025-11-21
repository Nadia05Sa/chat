from pymongo import MongoClient
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config import MONGO_URI, DB_NAME

class DBManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.conectado = False

    def conectar(self):
        if not self.conectado:
            print("[DB] Conectando a MongoDB...")
            self.client = MongoClient(MONGO_URI)
            self.db = self.client[DB_NAME]
            self.conectado = True
            print("[DB] Conectado correctamente.")

    # -------------------------------------------------------
    # USUARIOS CLÁSICOS
    # -------------------------------------------------------
    def crear_usuario_classico(self, nombre, apellido, email, password, ip):
        self.conectar()
        usuarios = self.db.usuarios

        if usuarios.find_one({"email": email}):
            return None

        user = {
            "nombre": nombre,
            "apellido": apellido,
            "email": email,
            "password_hash": generate_password_hash(password),
            "ip_registro": ip,
            "google_id": None,
            "foto": None,
            "fecha_registro": datetime.utcnow(),
        }

        result = usuarios.insert_one(user)
        return str(result.inserted_id)

    def login_usuario_classico(self, email, password, ip):
        self.conectar()
        usuarios = self.db.usuarios

        user = usuarios.find_one({"email": email})
        if not user:
            return None

        if not check_password_hash(user["password_hash"], password):
            return None

        usuarios.update_one(
            {"_id": user["_id"]},
            {"$set": {"ip_ultimo_login": ip, "ultimo_login": datetime.utcnow()}}
        )

        return str(user["_id"])

    # -------------------------------------------------------
    # USUARIOS GOOGLE
    # -------------------------------------------------------
    def crear_o_actualizar_usuario_google(self, nombre, apellido, google_id, email, foto, ip):
        self.conectar()
        usuarios = self.db.usuarios

        user = usuarios.find_one({"google_id": google_id})

        if user:
            usuarios.update_one(
                {"_id": user["_id"]},
                {"$set": {"ultimo_login": datetime.utcnow(), "ip_ultimo_login": ip}}
            )
            return str(user["_id"])

        nuevo = {
            "nombre": nombre,
            "apellido": apellido,
            "google_id": google_id,
            "email": email,
            "foto": foto,
            "password_hash": None,
            "fecha_registro": datetime.utcnow(),
            "ip_registro": ip,
        }

        result = usuarios.insert_one(nuevo)
        return str(result.inserted_id)

    # -------------------------------------------------------
    # PERFIL / ESTADÍSTICAS
    # -------------------------------------------------------
    def obtener_estadisticas_usuario(self, usuario_id):
        self.conectar()
        from bson.objectid import ObjectId

        user = self.db.usuarios.find_one({"_id": ObjectId(usuario_id)}, {"password_hash": 0})
        return user

    # -------------------------------------------------------
    # CANALES
    # -------------------------------------------------------
    def obtener_canales_db(self):
        self.conectar()
        return list(self.db.canales.find({}, {"_id": 0}))

    def obtener_canales_donde_estoy(self, usuario_id):
        self.conectar()
        return list
