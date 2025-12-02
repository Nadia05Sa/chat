# db_manager.py
from datetime import datetime
from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from bson import ObjectId
from config import MONGO_URI, DB_NAME
from passlib.hash import bcrypt
from security import cifrar_aes_cbc


class DatabaseManager:
    """Gestor de base de datos MongoDB (IDs como ObjectId para todo)."""

    def __init__(self, uri: str, db_name: str):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None
        self.conectado = False

    # -------------------------------
    # CONEXIÓN
    # -------------------------------
    def conectar(self) -> bool:
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Ping para verificar conexión
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            self.conectado = True
            self._inicializar_colecciones()
            print(f"[+] Conectado a MongoDB: {self.db_name}")
            return True
        except ConnectionFailure as e:
            print(f"[x] Error al conectar a MongoDB: {e}")
            self.conectado = False
            return False

    # -------------------------------
    # INICIALIZACIÓN (colecciones + índices)
    # -------------------------------
    def _inicializar_colecciones(self):
        if not self.conectado:
            return

        # Crear colecciones si no existen (no falla si ya existen)
        if "usuarios" not in self.db.list_collection_names():
            self.db.create_collection("usuarios")
        if "mensajes" not in self.db.list_collection_names():
            self.db.create_collection("mensajes")
        if "sesiones" not in self.db.list_collection_names():
            self.db.create_collection("sesiones")
        if "canales" not in self.db.list_collection_names():
            self.db.create_collection("canales")

        # Índices recomendados
        # google_id único si existe (partial index)
        try:
            self.db.usuarios.create_index(
                [("google_id", 1)],
                unique=True,
                partialFilterExpression={"google_id": {"$exists": True, "$ne": None}}
            )
        except Exception:
            pass

        # nombres no únicos
        try:
            self.db.usuarios.create_index("nombre")
            self.db.usuarios.create_index("activo")
        except Exception:
            pass

        # mensajes
        try:
            self.db.mensajes.create_index("usuario_id")
            self.db.mensajes.create_index("canal_id")
            self.db.mensajes.create_index("timestamp")
        except Exception:
            pass

        # sesiones
        try:
            self.db.sesiones.create_index("usuario_id")
            self.db.sesiones.create_index("inicio")
            self.db.sesiones.create_index("fin")
        except Exception:
            pass

        # canales: nombre único
        try:
            self.db.canales.create_index("nombre", unique=True)
        except Exception:
            pass

        print("[+] Colecciones e indices inicializados")

    # -------------------------------
    # USUARIOS
    # -------------------------------

    def cambiar_estado_usuario(self, usuario_id: str, activo: bool) -> bool:
        """Marca usuario como activo/inactivo. Devuelve True si modificado."""
        if not self.conectado:
            return False
        try:
            res = self.db.usuarios.update_one(
                {"_id": ObjectId(usuario_id)},
                {"$set": {"activo": activo, "ultima_conexion": datetime.utcnow()}}
            )
            return res.modified_count > 0
        except Exception as e:
            print(f"[DB ERROR] cambiar_estado_usuario: {e}")
            return False

    def obtener_estadisticas_usuario(self, usuario_id_or_nombre):
        """Si recibe id (str) busca por _id, si recibe nombre busca por nombre."""
        if not self.conectado:
            return None
        try:
            if isinstance(usuario_id_or_nombre, str) and ObjectId.is_valid(usuario_id_or_nombre):
                user = self.db.usuarios.find_one({"_id": ObjectId(usuario_id_or_nombre)})
            else:
                user = self.db.usuarios.find_one({"nombre": usuario_id_or_nombre})
            if not user:
                return None
            # convertir ObjectId a str para facilidad
            user["_id"] = str(user["_id"])
            return user
        except Exception as e:
            print(f"[DB ERROR] obtener_estadisticas_usuario: {e}")
            return None
        
  # ----------------------------
    # Registro clásico
    # ----------------------------
    def crear_usuario_classico(self, nombre: str, apellido: str, email: str, password: str, ip: str = None):
        if not nombre or not email or not password:
            return None

        # Truncar password a 72 bytes
        password_bytes = password.encode("utf-8")[:72]
        hashed_pw = bcrypt.hash(password_bytes)

        now = datetime.utcnow()
        doc = {
            "nombre": nombre,
            "apellido": apellido,
            "email": email,
            "password": hashed_pw,
            "google_id": None,
            "picture":None,
            "primera_conexion": now,
            "ultima_conexion": now,
            "ip_ultima": ip,
            "activo": True,
            "total_conexiones": 1,
            "total_mensajes": 0
        }
        
        try:
            res = self.db.usuarios.insert_one(doc)
            return str(res.inserted_id)
        except DuplicateKeyError as e :
            # Email ya existe
            return None

    # ----------------------------
    # Login clásico
    # ----------------------------
    def login_usuario_classico(self, email: str, password: str, ip: str = None):
        if not email or not password:
            return None

        user = self.db.usuarios.find_one({"email": email})
        if not user:
            return None

        password_bytes = password.encode("utf-8")[:72]

        if not bcrypt.verify(password_bytes, user["password"]):
            return None

        # actualizar última conexión
        self.db.usuarios.update_one(
            {"_id": user["_id"]},
            {"$set": {"ultima_conexion": datetime.utcnow(), "ip_ultima": ip},
             "$inc": {"total_conexiones": 1}}
        )

        return str(user["_id"])

    # ----------------------------
    # Registro / login con Google ID
    # ----------------------------
    def crear_o_actualizar_usuario_google(self, nombre: str,  apellido: str, google_id: str, email: str, picture: str, ip: str = None):
        if not google_id:
            return None

        now = datetime.utcnow()
        query = {"$or": [{"google_id": google_id}, {"nombre": nombre}]}
        update = {
            "$set": {
                "nombre": nombre,
                "apellido":apellido,
                "email": email,
                "password": None,
                "google_id": google_id,
                "picture":picture,
                "ultima_conexion": now,
                "ip_ultima": ip,
                "activo": True
            },
            "$setOnInsert": {
                "primera_conexion": now,
                "total_mensajes": 0
            },
            "$inc": {"total_conexiones": 1}
        }

        res = self.db.usuarios.update_one(query, update, upsert=True)
        if res.upserted_id:
            return str(res.upserted_id)
        # devolver id del usuario existente
        existing = self.db.usuarios.find_one({"google_id": google_id})
        if existing:
            return str(existing["_id"])
        return None
    
    def obtener_usuarios(self):
        if not self.conectado:
            return []
        try:
            return [
                {**u, "_id": str(u["_id"])}
                for u in self.db.usuarios.find()
            ]
        except Exception as e:
            print("[DB ERROR] obtener_usuarios:", e)
            return []
        
    def validar_usuario_ws(self, usuario_id: str, google_id: str | None):
        """
        Valida que el usuario exista.
        - Si google_id viene -> verificar ambos.
        - Si google_id es None -> verificar solo usuario_id.
        """
        if not self.conectado:
            return None

        try:
            query = {"_id": ObjectId(usuario_id)}

            # Si el usuario se autenticó con Google, validar que coincida
            if google_id:
                query["google_id"] = google_id

            user = self.db.usuarios.find_one(query)

            return user

        except Exception as e:
            print(f"[DB ERROR] validar_usuario_ws: {e}")
            return None

    # -------------------------------
    # SESIONES
    # -------------------------------
    def registrar_sesion(self, usuario_id: str, tipo: str = "inicio"):
        """
        Registra inicio o fin de sesión.
        - tipo == 'inicio' -> inserta documento con inicio, devuelve id sesión (str)
        - tipo == 'fin' -> actualiza la sesión activa, devuelve modified_count
        """
        if not self.conectado:
            return None
        try:
            if tipo == "inicio":
                doc = {
                    "usuario_id": ObjectId(usuario_id),
                    "inicio": datetime.utcnow(),
                    "fin": None,
                    "activa": True
                }
                res = self.db.sesiones.insert_one(doc)
                return str(res.inserted_id)
            else:
                res = self.db.sesiones.update_one(
                    {"usuario_id": ObjectId(usuario_id), "activa": True},
                    {"$set": {"fin": datetime.utcnow(), "activa": False}}
                )
                return res.modified_count
        except Exception as e:
            print(f"[DB ERROR] registrar_sesion: {e}")
            return None

    # -------------------------------
    # CANALES (persistentes)
    # -------------------------------
    def crear_canal(self, nombre: str, creador_id: str) -> str | None:
        """
        Crea un canal en Mongo, validando duplicados.
        Guarda creador_id (ObjectId) y agrega al creador en miembros/admins.
        Devuelve id (str) si creado, None si ya existe o error.
        """
        if not self.conectado:
            return None
        try:
            # validar duplicado
            existente = self.db.canales.find_one({"nombre": nombre})
            if existente:
                return None

            canal_doc = {
                "nombre": nombre,
                "creador_id": ObjectId(creador_id),
                "admins": [ObjectId(creador_id)],  # el creador es admin por defecto
                "miembros": [ObjectId(creador_id)],
                "publico": True,
                "fecha_creacion": datetime.now()
            }
            
            res = self.db.canales.insert_one(canal_doc)
            return str(res.inserted_id)
        except Exception as e:
            print(f"[DB ERROR] crear_canal: {e}")
            return None
        
    def crear_canal_privado(self, nombre: str, creador_id: str) -> str | None:
        """
        Crea un canal en Mongo, validando duplicados.
        Guarda creador_id (ObjectId) y agrega al creador en miembros/admins.
        Devuelve id (str) si creado, None si ya existe o error.
        """
        if not self.conectado:
            return None
        try:
            # validar duplicado
            existente = self.db.canales.find_one({"nombre": nombre})
            if existente:
                return None

            canal_doc = {
                "nombre": nombre,
                "creador_id": ObjectId(creador_id),
                "admins": [ObjectId(creador_id)],  # el creador es admin por defecto
                "miembros": [ObjectId(creador_id)],
                "publico": False,
                "fecha_creacion": datetime.now()
            }
            
            res = self.db.canales.insert_one(canal_doc)
            return str(res.inserted_id)
        except Exception as e:
            print(f"[DB ERROR] crear_canal: {e}")
            return None
        
    def obtener_ultimo_mensaje(self, canal_id):
        """
        Devuelve el mensaje más reciente de un canal en formato:
        {"usuario_id": str, "contenido": str, "fecha": datetime, "hash": str}
        """
        
        if not self.conectado:
            return None
        try:
            # Buscar el mensaje más reciente por fecha
            doc = self.db.mensajes.find_one(
                {"canal_id": ObjectId(canal_id)},  # Filtra por canal
                sort=[("timestamp", -1)]                # Orden descendente por fecha
            )
            if not doc:
                return None
            
            usuario =  self.db.usuarios.find_one(doc["usuario_id"])

            return {
                "usuario_id": str(doc["usuario_id"]),
                "usuario_nombre": usuario["nombre"],
                "contenido": doc["mensaje"],
                "fecha": doc.get("timestamp").isoformat()
            }
        except Exception as e:
            print(f"[DB ERROR] obtener_ultimo_mensaje: {e}")
            return None

    def obtener_canales_db(self) -> list:
        """
        Devuelve lista de canales con forma: [{"_id": str, "nombre": str, "creador_id": str, "admins":[str, ...]}]
        """
        if not self.conectado:
            return []
        try:
            docs = self.db.canales.find({}, {"nombre": 1, "creador_id": 1, "admins": 1, "miembros": 1, "fecha_creacion": 1, "publico": 1})
            salida = []
            for c in docs:
                salida.append({
                    "_id": str(c["_id"]),
                    "nombre": c.get("nombre"),
                    "creador_id": str(c.get("creador_id")) if c.get("creador_id") else None,
                    "admins": [str(a) for a in c.get("admins", [])],
                    "miembros": [str(a) for a in c.get("miembros", [])],
                    "publico": c.get("publico"),
                    "fecha_creacion":c.get("fecha_creacion").isoformat(),
                     "ultimo": self.obtener_ultimo_mensaje(c.get("_id"))
                })
            return salida
        except Exception as e:
            print(f"[DB ERROR] obtener_canales_db: {e}")
            return []

    def obtener_canales_donde_estoy(self, usuario_id) -> list:
        """
        Devuelve lista de canales con forma: [{"_id": str, "nombre": str, "creador_id": str, "admins":[str, ...]}]
        """
        if not self.conectado:
            return []
        try:
            usuario_objid = ObjectId(usuario_id)
            docs = self.db.canales.find({
                "$or": [
                    {"miembros": {"$in": [usuario_objid]}},
                    {"admins":  {"$in": [usuario_objid]}}
                ]
            },{"nombre": 1, "creador_id": 1, "admins": 1, "miembros": 1, "fecha_creacion": 1, "publico": 1})
            salida = []
            for c in docs:
                salida.append({
                    "_id": str(c["_id"]),
                    "nombre": c.get("nombre"),
                    "creador_id": str(c.get("creador_id")) if c.get("creador_id") else None,
                    "admins": [str(a) for a in c.get("admins", [])],
                    "miembros": [str(a) for a in c.get("miembros", [])],
                    "publico": c.get("publico"),
                    "fecha_creacion":c.get("fecha_creacion").isoformat(),
                     "ultimo": self.obtener_ultimo_mensaje(c.get("_id"))
                })
            return salida
        except Exception as e:
            print(f"[DB ERROR] obtener_canales_db: {e}")
            return []

    def obtener_canal_doc_por_nombre(self, nombre: str) -> dict | None:
        """Devuelve documento del canal (con ids string) o None."""
        if not self.conectado:
            return None
        try:
            c = self.db.canales.find_one({"nombre": nombre})
            if not c:
                return None
            return {
                "_id": str(c["_id"]),
                "nombre": c.get("nombre"),
                "creador_id": str(c.get("creador_id")) if c.get("creador_id") else None,
                "admins": [str(a) for a in c.get("admins", [])],
                "miembros": [str(m) for m in c.get("miembros", [])],
                "publico": c.get("publico", True),
                "fecha_creacion": c.get("fecha_creacion").isoformat() if c.get("fecha_creacion") else None,
                "ultimo": self.obtener_ultimo_mensaje(c.get("_id"))
            }
        except Exception as e:
            print(f"[DB ERROR] obtener_canal_doc_por_nombre: {e}")
            return None

    def agregar_usuario_a_canal(self, canal_id: str, email: str) -> bool:
        """Agrega usuario (ObjectId) a miembros[]. Devuelve True si modificado."""
        if not self.conectado:
            return False
        try:
            user = self.db.usuarios.find_one({"email": email})
            res = self.db.canales.update_one(
                {"_id": ObjectId(canal_id)},
                {"$addToSet": {"miembros": ObjectId(user["_id"])}}
            )
            return res.modified_count > 0 or res.matched_count > 0
        except Exception as e:
            print(f"[DB ERROR] agregar_usuario_a_canal: {e}")
            return False

    def agregar_usuario_a_canal_por_id(self, canal_id: str,  usuario_id: str) -> bool:
        """Agrega usuario (ObjectId) a miembros[]. Devuelve True si modificado."""
        if not self.conectado:
            return False
        try:
            user = self.db.usuarios.find_one({"_id": ObjectId(usuario_id)})
            res = self.db.canales.update_one(
                {"_id": ObjectId(canal_id)},
                {"$addToSet": {"miembros": ObjectId(user["_id"])}}
            )
            return res.modified_count > 0 or res.matched_count > 0
        except Exception as e:
            print(f"[DB ERROR] agregar_usuario_a_canal: {e}")
            return False

    def remover_usuario_de_canal(self, canal_id: str, email: str) -> bool:
        """Remueve usuario de miembros[]."""
        if not self.conectado:
            return False
        try:
            user = self.db.usuarios.find_one({"email": email})
            res = self.db.canales.update_one(
                {"_id": ObjectId(canal_id)},
                {"$pull": {"miembros": ObjectId(user["_id"])}}
            )
            return res.modified_count > 0
        except Exception as e:
            print(f"[DB ERROR] remover_usuario_de_canal: {e}")
            return False

    def agregar_admin(self, canal_id: str, email: str) -> bool:
        """Añade usuario a admins[]."""
        if not self.conectado:
            return False
        try:
            user = self.db.usuarios.find_one({"email": email})
            res = self.db.canales.update_one(
                {"_id": ObjectId(canal_id)},
                {"$addToSet": {"admins": ObjectId(user["_id"])}}
            )
            return res.modified_count > 0 or res.matched_count > 0
        except Exception as e:
            print(f"[DB ERROR] agregar_admin: {e}")
            return False

    def remover_admin(self, canal_id: str, email: str) -> bool:
        """Quita usuario de admins[]."""
        if not self.conectado:
            return False
        try:
            user = self.db.usuarios.find_one({"email": email})
            res = self.db.canales.update_one(
                {"_id": ObjectId(canal_id)},
                {"$pull": {"admins": ObjectId(user["_id"])}}
            )
            return res.modified_count > 0
        except Exception as e:
            print(f"[DB ERROR] remover_admin: {e}")
            return False
        
    def es_admin(self, canal_id: str, usuario_id: str) -> bool:
        canal = self.obtener_canal_por_id(canal_id)
        return canal and usuario_id in canal["admins"]

    def borrar_canal(self, canal_id: str) -> bool:
        """Elimina el canal por id (ObjectId)."""
        if not self.conectado:
            return False
        try:
            res = self.db.canales.delete_one({"_id": ObjectId(canal_id)})
            return res.deleted_count > 0
        except Exception as e:
            print(f"[DB ERROR] borrar_canal: {e}")
            return False

    def salir_de_canal(self, usuario_id: str, canal_id: str) -> bool:
        """
        Quita al usuario de miembros y administradores del canal,
        pero NO permite salir si el canal quedaría sin administradores.
        Devuelve True si salió, False si no fue posible.
        """
        if not self.conectado:
            return False

        try:
            canal = self.db.canales.find_one({"_id": ObjectId(canal_id)})
            if not canal:
                return False

            usuario_obj = ObjectId(usuario_id)

            # Si el usuario es admin, verificar si es el último
            if usuario_obj in canal.get("administradores", []):
                num_admins = len(canal.get("administradores", []))

                # Si es el último admin, NO permitimos salir
                if num_admins <= 1:
                    print("[INFO] No puedes salir: solo hay un administrador.")
                    return False

            # Si pasa esta validación, sí se puede salir
            res = self.db.canales.update_one(
                {"_id": ObjectId(canal_id)},
                {
                    "$pull": {
                        "miembros": usuario_obj,
                        "administradores": usuario_obj
                    }
                }
            )

            return res.modified_count > 0 or res.matched_count > 0

        except Exception as e:
            print(f"[DB ERROR] salir_de_canal: {e}")
            return False
    
    # -------------------------------
    # MENSAJES
    # -------------------------------
    def guardar_mensaje(self, usuario_id: str, canal_id: str, mensaje: str, hash_sha256: str) -> str | None:
        """
        Guarda un mensaje referenciando usuario_id y canal_id (ObjectId).
        Devuelve id de mensaje (str) o None en error.
        """
        if not self.conectado:
            return None
        try:
            doc = {
                "usuario_id": ObjectId(usuario_id),
                "canal_id": ObjectId(canal_id),
                "mensaje": mensaje,
                "hash_sha256": hash_sha256,
                "longitud": len(mensaje),
                "timestamp": datetime.utcnow()
            }
            res = self.db.mensajes.insert_one(doc)
            # incrementar contador de mensajes del usuario (no crítico)
            try:
                self.db.usuarios.update_one(
                    {"_id": ObjectId(usuario_id)},
                    {"$inc": {"total_mensajes": 1}}
                )
            except Exception:
                pass
            return str(res.inserted_id)
        except Exception as e:
            print(f"[DB ERROR] guardar_mensaje: {e}")
            return None

    # -------------------------------
    # HISTORIAL
    # -------------------------------
    def obtener_historial(self, canal_id: str, limite: int = 50) -> list:
        """
        Obtiene historial de mensajes por canal_id (devuelve lista de documentos con campos legibles).
        """
        if not self.conectado:
            return []
        try:
            cursor = self.db.mensajes.find({"canal_id": ObjectId(canal_id)}).sort("timestamp", DESCENDING).limit(limite)
            mensajes = []
            for m in cursor:
                mensajes.append({
                    "_id": str(m["_id"]),
                    "usuario_id": str(m["usuario_id"]),
                    "mensaje": m["mensaje"],
                    "hash_sha256": m.get("hash_sha256"),
                    "longitud": m.get("longitud"),
                    "timestamp": m.get("timestamp").isoformat() if m.get("timestamp") else None
                })
            return list(reversed(mensajes))
        except Exception as e:
            print(f"[DB ERROR] obtener_historial: {e}")
            return []

    # -------------------------------
    # BÚSQUEDAS / UTILIDADES
    # -------------------------------
    def buscar_por_hash(self, hash_sha256: str):
        if not self.conectado:
            return None
        try:
            m = self.db.mensajes.find_one({"hash_sha256": hash_sha256})
            if not m:
                return None
            m["_id"] = str(m["_id"])
            m["usuario_id"] = str(m["usuario_id"])
            m["canal_id"] = str(m["canal_id"])
            return m
        except Exception as e:
            print(f"[DB ERROR] buscar_por_hash: {e}")
            return None

    def obtener_canal_por_id(self, canal_id: str) -> dict | None:
        """Devuelve documento de canal con ids string o None."""
        if not self.conectado:
            return None
        try:
            c = self.db.canales.find_one({"_id": ObjectId(canal_id)})
            if not c:
                return None
            return {
                "_id": str(c["_id"]),
                "nombre": c.get("nombre"),
                "creador_id": str(c.get("creador_id")) if c.get("creador_id") else None,
                "admins": [str(a) for a in c.get("admins", [])],
                "miembros": [str(m) for m in c.get("miembros", [])],
                "publico": c.get("publico", True),
                "fecha_creacion": c.get("fecha_creacion")
            }
        except Exception as e:
            print(f"[DB ERROR] obtener_canal_por_id: {e}")
            return None

    # -------------------------------
    # ESTADÍSTICAS GENERALES
    # -------------------------------
    def obtener_estadisticas_generales(self) -> dict:
        if not self.conectado:
            return {}
        try:
            stats = {
                "total_usuarios": self.db.usuarios.count_documents({}),
                "total_mensajes": self.db.mensajes.count_documents({}),
                "sesiones_activas": self.db.sesiones.count_documents({"activa": True}),
                "total_sesiones": self.db.sesiones.count_documents({})
            }
            return stats
        except Exception as e:
            print(f"[DB ERROR] obtener_estadisticas_generales: {e}")
            return {}

    # -------------------------------
    # TOKENS DE AUTORIZACIÓN (Firma Digital)
    # -------------------------------
    def obtener_usuario_por_email(self, email: str) -> dict | None:
        """Busca usuario por email. Devuelve documento con _id string o None."""
        if not self.conectado:
            return None
        try:
            user = self.db.usuarios.find_one({"email": email})
            if not user:
                return None
            return {
                "_id": str(user["_id"]),
                "nombre": user.get("nombre"),
                "apellido": user.get("apellido"),
                "email": user.get("email"),
                "picture": user.get("picture"),
                "activo": user.get("activo", False)
            }
        except Exception as e:
            print(f"[DB ERROR] obtener_usuario_por_email: {e}")
            return None

    def guardar_token_autorizacion(self, token: str, usuario_email: str, archivo_id: str, 
                                    permisos: list, expiracion: datetime, solicitante_id: str) -> bool:
        """Guarda un token de autorización en la base de datos."""
        if not self.conectado:
            return False
        try:
            # Crear colección si no existe
            if "tokens_firma" not in self.db.list_collection_names():
                self.db.create_collection("tokens_firma")
                self.db.tokens_firma.create_index("token", unique=True)
                self.db.tokens_firma.create_index("expiracion")
            
            doc = {
                "token": token,
                "usuario_email": usuario_email,
                "archivo_id": archivo_id,
                "permisos": permisos,
                "expiracion": expiracion,
                "solicitante_id": solicitante_id,
                "usado": False,
                "fecha_creacion": datetime.utcnow()
            }
            self.db.tokens_firma.insert_one(doc)
            return True
        except Exception as e:
            print(f"[DB ERROR] guardar_token_autorizacion: {e}")
            return False

    def obtener_token_autorizacion(self, token: str) -> dict | None:
        """Obtiene información de un token de autorización."""
        if not self.conectado:
            return None
        try:
            doc = self.db.tokens_firma.find_one({"token": token})
            if not doc:
                return None
            return {
                "token": doc["token"],
                "usuario_email": doc["usuario_email"],
                "archivo_id": doc["archivo_id"],
                "permisos": doc.get("permisos", []),
                "expiracion": doc["expiracion"],
                "solicitante_id": doc.get("solicitante_id"),
                "usado": doc.get("usado", False),
                "fecha_creacion": doc.get("fecha_creacion")
            }
        except Exception as e:
            print(f"[DB ERROR] obtener_token_autorizacion: {e}")
            return None

    def marcar_token_usado(self, token: str) -> bool:
        """Marca un token como usado."""
        if not self.conectado:
            return False
        try:
            res = self.db.tokens_firma.update_one(
                {"token": token},
                {"$set": {"usado": True, "fecha_uso": datetime.utcnow()}}
            )
            return res.modified_count > 0
        except Exception as e:
            print(f"[DB ERROR] marcar_token_usado: {e}")
            return False

    def limpiar_tokens_expirados(self) -> int:
        """Elimina tokens expirados. Devuelve cantidad eliminada."""
        if not self.conectado:
            return 0
        try:
            res = self.db.tokens_firma.delete_many({"expiracion": {"$lt": datetime.utcnow()}})
            return res.deleted_count
        except Exception as e:
            print(f"[DB ERROR] limpiar_tokens_expirados: {e}")
            return 0

    # -------------------------------
    # CERRAR
    # -------------------------------
    def cerrar(self):
        if self.client:
            self.client.close()
            print("[+] Conexion MongoDB cerrada")


# instancia global
db_manager = DatabaseManager(MONGO_URI, DB_NAME)