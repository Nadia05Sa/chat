# index.py
from flask import Blueprint, render_template, request, jsonify, url_for, session, redirect
from db_manager import db_manager
from config import oauth

rutas = Blueprint("rutas", __name__)

def get_google():
    return oauth.create_client("google")


# ------------------------------------------------
# Páginas principales
# ------------------------------------------------
@rutas.get("/login")
def login_page():
    return render_template("login.html")


@rutas.get("/chat")
def chat_page():
    if "user" not in session:
        return redirect("/login")
    return render_template("chat.html")


@rutas.get("/perfil")
def perfil_page():
    if "user" not in session:
        return redirect("/login")
    return render_template("perfil.html")


@rutas.get("/denied")
def access_denied_page():
    return render_template("denied.html")


# ------------------------------------------------
# Registro clásico
# ------------------------------------------------
@rutas.post("/register")
def register():
    data = request.json

    nombre = data.get("nombre")
    apellido = data.get("apellido")
    email = data.get("email")
    password = data.get("password")
    ip = request.remote_addr

    if not nombre or not apellido or not email or not password:
        return jsonify({"error": "Faltan campos"}), 400

    uid = db_manager.registrar_clasico(nombre, apellido, email, password, ip)
    if not uid:
        return jsonify({"error": "Email ya registrado"}), 409

    return jsonify({"user_id": uid}), 201


# ------------------------------------------------
# Login clásico
# ------------------------------------------------
@rutas.post("/login")
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    ip = request.remote_addr

    if not email or not password:
        return jsonify({"error": "Faltan campos"}), 400

    uid = db_manager.login_clasico(email, password, ip)
    if not uid:
        return jsonify({"error": "Email o contraseña incorrectos"}), 401

    # Guardamos usuario en sesión
    session["user"] = {
        "_id": uid,
        "email": email,
        "login_method": "classic"
    }

    return jsonify({"user_id": uid})


# ------------------------------------------------
# Login con Google OAuth
# ------------------------------------------------
@rutas.get("/login_google")
def login_google():
    google = get_google()
    redirect_uri = url_for("rutas.auth", _external=True)
    return google.authorize_redirect(redirect_uri, prompt="select_account")


@rutas.get("/auth")
def auth():
    google = get_google()
    token = google.authorize_access_token()

    user_info = google.get("userinfo", token=token).json()
    ip = request.remote_addr

    # Guardar/crear usuario en BD
    nombre = user_info.get("given_name")
    apellido = user_info.get("family_name")
    google_id = user_info.get("id")
    email = user_info.get("email")
    picture = user_info.get("picture")

    # Guardar registro/auditoria
    db_manager.auditoria("login_google", email)

    # Guardar en sesión
    session["user"] = {
        "_id": google_id,
        "google_id": google_id,
        "email": email,
        "name": user_info.get("name"),
        "picture": picture,
        "login_method": "google"
    }

    return redirect("/chat")


# ------------------------------------------------
# Ver usuario en sesión
# ------------------------------------------------
@rutas.get("/session_user")
def session_user():
    if "user" not in session:
        return jsonify({"logged": False})

    return jsonify({
        "logged": True,
        "user": session["user"]
    })


# ------------------------------------------------
# Canales
# ------------------------------------------------
@rutas.get("/canales")
def obtener_canales():
    return jsonify(db_manager.obtener_canales())


@rutas.get("/canales/<canal_id>/mensajes")
def obtener_mensajes_por_canal(canal_id):
    # NO existe historial en tu db_manager actual,
    # pero dejo el endpoint preparado.
    return jsonify({"error": "Historial no implementado"}), 501


# ------------------------------------------------
# Usuarios
# ------------------------------------------------
@rutas.get("/usuarios")
def obtener_usuarios():
    users = db_manager.db.usuarios.find()
    lista = [{**u, "_id": str(u["_id"])} for u in users]
    return jsonify(lista)
