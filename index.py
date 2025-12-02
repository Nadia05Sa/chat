# index.py
from flask import Blueprint, render_template, request, jsonify, url_for, session, redirect
from db_manager import db_manager
from config import oauth

rutas = Blueprint("rutas", __name__)

def get_google():
    return oauth.create_client("google")

@rutas.get("/login")
def login_page():
    # Capturar URL de redirección y mensaje
    next_url = request.args.get('next', '')
    msg = request.args.get('msg', '')
    return render_template("login.html", next_url=next_url, login_msg=msg)

@rutas.route('/login_google')
def login_google():
    google = get_google()
    redirect_uri = url_for('rutas.auth', _external=True)
    # Guardar URL de redirección para después del auth
    next_url = request.args.get('next', '')
    if next_url:
        session['login_next'] = next_url
    return google.authorize_redirect(redirect_uri, prompt="select_account")

@rutas.post("/register")
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    nombre = data.get("nombre")
    apellido = data.get("apellido")
    ip = request.remote_addr

    if not email or not password or not nombre or not apellido:
        return jsonify({"error": "Faltan campos"}), 400

    user_id = db_manager.crear_usuario_classico(nombre, apellido, email, password, ip)
    if not user_id:
        return jsonify({"error": "Email ya registrado"}), 409

    # Guardar sesion del usuario registrado
    session['user'] = {
        '_id': user_id,
        'google_id': None,
        'email': email,
        'name': nombre,
        'picture': None
    }

    return jsonify({"user_id": user_id}), 201

@rutas.route('/auth')
def auth():
    google = get_google()
    token = google.authorize_access_token()
    # token es un diccionario con access_token, id_token, etc.
    resp = google.get('userinfo', token=token)
    ip = request.remote_addr
    user_info = resp.json()
    # Guardamos info esencial en sesión
    user = db_manager.crear_o_actualizar_usuario_google(user_info["given_name"],user_info["family_name"], user_info["id"], user_info["email"], user_info["picture"], ip)
    session['user'] = {
    '_id': user,
    'google_id': user_info.get('id'),
    'email': user_info.get('email'),
    'name': user_info.get('name'),
    'picture': user_info.get('picture')
    }
    # Guardar token si quieres mostrarlo (solo para pruebas locales)
    session['token'] = token
    
    # Redirigir a URL guardada o al chat
    next_url = session.pop('login_next', None)
    if next_url:
        from urllib.parse import unquote
        return redirect(unquote(next_url))
    return redirect("/chat")

@rutas.post("/login")
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    ip = request.remote_addr

    if not email or not password:
        return jsonify({"error": "Faltan campos"}), 400

    user_id = db_manager.login_usuario_classico(email, password, ip)
    if not user_id:
        return jsonify({"error": "Email o contraseña incorrectos"}), 401

    # Obtener datos del usuario para la sesion
    usuario = db_manager.obtener_estadisticas_usuario(user_id)
    if usuario:
        session['user'] = {
            '_id': user_id,
            'google_id': None,
            'email': email,
            'name': usuario.get('nombre', email),
            'picture': usuario.get('picture')
        }

    return jsonify({"user_id": user_id})

@rutas.get("/session_user")
def session_user():
    if "user" not in session:
        return jsonify({"logged": False})

    return jsonify({
        "logged": True,
        "user": {
            "_id": session["user"]["_id"],
            "google_id": session["user"]["google_id"],
            "email": session["user"]["email"],
            "name": session["user"]["name"],
            "picture": session["user"]["picture"]
        }
    })

@rutas.get("/chat")
def chat_page():
    return render_template("chat.html")

@rutas.get("/perfil")
def perfil_page():
    return  render_template("perfil.html")

@rutas.get("/denied")
def access_denied_page():
    return  render_template("denied.html")

@rutas.get("/perfil/<usuario_id>")
def perfil(usuario_id):
    usuario = db_manager.obtener_estadisticas_usuario(usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(usuario)

@rutas.get("/canales")
def obtener_canales():
    lista = db_manager.obtener_canales_db()
    return lista

@rutas.get("/canales/<usuario_id>")
def obtener_canales_filtrados(usuario_id):
    lista = db_manager.obtener_canales_donde_estoy(usuario_id)
    return lista

@rutas.get("/canales/<canal_id>/mensajes")
def obtener_mensajes_por_canal(canal_id):
    lista = db_manager.obtener_historial(canal_id)
    return lista

@rutas.get("/usuarios")
def obtener_usuarios():
    lista = db_manager.obtener_usuarios()
    return jsonify(lista)