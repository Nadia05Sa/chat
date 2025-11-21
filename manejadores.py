import json
from datetime import datetime
from db_manager import db_manager
from bson import ObjectId
from security import escribir_log_auditoria, calcular_hash_sha256, crear_hmac, descifrar_aes_cbc

# -------------------------
# CONEXIONES EN MEMORIA
# -------------------------

clientes = {}          # websocket → usuario_id
usuario_canal = {}     # websocket → canal_id
canal_general_id = None   # se asignará al iniciar servidor

# ============================================================
# BROADCAST SOLO A MIEMBROS DEL CANAL
# ============================================================
async def broadcast(canal_id, mensaje):
    for ws, canal_actual in usuario_canal.items():
        if canal_actual == canal_id:
            try:
                await ws.send(mensaje)
            except:
                pass

# ============================================================
# PROCESADOR DE COMANDOS
# ============================================================
async def procesar_comando(websocket, usuario_id, mensaje):
    partes = mensaje.split(" ", 1)
    comando = partes[0].lower()

    # -----------------------------
    # Crear canal público
    # -----------------------------
    if comando == "/crear":
        if len(partes) < 2:
            await websocket.send(json.dumps({
                "tipo": "error",
                "mensaje": "Uso: /crear nombre_del_canal"
            }))
            return True

        nombre = partes[1].strip()
        canal_id = db_manager.crear_canal(nombre, usuario_id)
        canales = db_manager.obtener_canales_donde_estoy(usuario_id)
        await websocket.send(json.dumps({
            "tipo": "comando",
            "comando": "/crear",
            "resultado": {
                "exito": bool(canal_id),
                "mensaje": f"Canal '{nombre}' creado con id {canal_id}" if canal_id else "❌ No se pudo crear. ¿Existe ya el nombre?"
            },
            "lista" : canales
        }))
        return True

    # -----------------------------
    # Crear canal privado
    # -----------------------------
    if comando == "/crear_priv":
        if len(partes) < 2:
            await websocket.send(json.dumps({
                "tipo": "error",
                "mensaje": "Uso: /crear_priv nombre_del_canal"
            }))
            return True

        nombre = partes[1].strip()
        canal_id = db_manager.crear_canal_privado(nombre, usuario_id)
        canales = db_manager.obtener_canales_donde_estoy(usuario_id)
        await websocket.send(json.dumps({
            "tipo": "comando",
            "comando": "/crear_priv",
            "resultado": {
                "exito": bool(canal_id),
                "mensaje": f"Canal '{nombre}' creado con id {canal_id}" if canal_id else "❌ No se pudo crear. ¿Existe ya el nombre?"
            },
            "lista" : canales
        }))
        return True

    # -----------------------------
    # Unirse a un canal
    # -----------------------------
    if comando == "/unir":
        if len(partes) < 2:
            await websocket.send(json.dumps({"tipo": "error","mensaje": "Uso: /unir nombre_del_canal"}))
            return True

        nombre = partes[1].strip()
        canal_doc = db_manager.obtener_canal_doc_por_nombre(nombre)
        if not canal_doc:
            await websocket.send(json.dumps({"tipo": "error", "mensaje": "❌ No existe ese canal"}))
            return True

        canal_id = str(canal_doc["_id"])
        db_manager.agregar_usuario_a_canal_por_id(canal_id, usuario_id)
        usuario_canal[websocket] = canal_id

        historial = []
        for m in db_manager.obtener_historial(canal_id):
            usuario = db_manager.validar_usuario_ws(m["usuario_id"], google_id=None)
            mensaje_cifrado = m.get("mensaje", "")
            try:
                mensaje_descifrado = descifrar_aes_cbc(mensaje_cifrado)
            except Exception:
                mensaje_descifrado = "<ERROR: no se pudo descifrar>"

            historial.append({
                "nombre": usuario["nombre"],
                "contenido": mensaje_cifrado,
                "fecha": m.get("timestamp") or datetime.utcnow().isoformat(),
                "hash": m.get("hash_sha256") 
            })

        await websocket.send(json.dumps({
            "tipo": "historial",
            "comando": "/unir",
            "contenido": f"Te uniste al canal {nombre} (id:{canal_id})",
            "mensajes": historial,
            "canal": canal_doc
        }))
        return True

    # -----------------------------
    # Salir al canal general
    # -----------------------------
    if comando == "/salir":
        canal_actual = usuario_canal.get(websocket)
        if not canal_actual or canal_actual == canal_general_id:
            await websocket.send(json.dumps({
                "tipo": "comando",
                "comando": "/salir",
                "resultado": "Ya estás en el canal general."
            }))
            return True

        db_manager.salir_de_canal(usuario_id, canal_actual)
        usuario_canal[websocket] = canal_general_id
        await websocket.send(json.dumps({"tipo": "comando","comando": "/salir","resultado": "Regresaste al canal general."}))
        return True

    # -----------------------------
    # Agregar usuario a canal (solo admin)
    # -----------------------------
    if comando == "/agregar" or comando == "/remover" or comando == "/dar_admin" or comando == "/quitar_admin":
        if len(partes) < 2:
            await websocket.send(json.dumps({"tipo": "error","mensaje": f"Uso: {comando} correo canal"}))
            return True

        try:
            email, nombre_canal = partes[1].strip().split(" ", 1)
        except ValueError:
            await websocket.send(json.dumps({"tipo": "error","mensaje": f"Uso: {comando} correo canal"}))
            return True

        canal_doc = db_manager.obtener_canal_doc_por_nombre(nombre_canal)
        if not canal_doc:
            await websocket.send(json.dumps({"tipo": "error", "mensaje": "❌ Canal no existe"}))
            return True

        canal_id = str(canal_doc["_id"])
        if usuario_id not in canal_doc["admins"]:
            await websocket.send(json.dumps({"tipo": "error", "mensaje": "❌ Solo admins pueden usar este comando"}))
            return True

        # Ejecutar la acción según el comando
        if comando == "/agregar":
            exito = db_manager.agregar_usuario_a_canal(canal_id, email)
            mensaje_resultado = "✅ Usuario agregado" if exito else "❌ No se pudo agregar"
        elif comando == "/remover":
            exito = db_manager.remover_usuario_de_canal(canal_id, email)
            mensaje_resultado = "✅ Usuario removido" if exito else "❌ No se pudo remover"
        elif comando == "/dar_admin":
            exito = db_manager.agregar_admin(canal_id, email)
            mensaje_resultado = "✅ Admin agregado" if exito else "❌ No se pudo agregar"
        elif comando == "/quitar_admin":
            exito = db_manager.remover_admin(canal_id, email)
            mensaje_resultado = "✅ Admin removido" if exito else "❌ No se pudo remover"

        # Registrar en log cada acción administrativa
        accion = f"{comando} {email} en canal {nombre_canal}"
        escribir_log_auditoria(usuario["nombre"], accion, calcular_hash_sha256(accion))

        await websocket.send(json.dumps({"tipo": "comando","comando": comando,"resultado": mensaje_resultado}))
        return True

    return False

# ============================================================
# MANEJADOR PRINCIPAL DEL CLIENTE
# ============================================================
async def manejar_cliente(websocket):
    try:
        # ================================
        # 1. PRIMER MENSAJE → identificación
        # ================================
        raw = await websocket.recv()
        data = json.loads(raw)
        
        usuario_id = data.get("usuario_id")
        google_id = data.get("google_id")  # puede ser None

        if not usuario_id:
            await websocket.send(json.dumps({
                "tipo": "error",
                "mensaje": "Falta usuario_id"
            }))
            return

        # ================================
        # 2. VALIDACIÓN EN MONGO
        # ================================
        usuario = db_manager.validar_usuario_ws(usuario_id, google_id)
        if not usuario:
            await websocket.send(json.dumps({
                "tipo": "error",
                "mensaje": "Usuario no existe o google_id incorrecto"
            }))
            await websocket.close()
            return

        # ================================
        # 3. REGISTRO WS
        # ================================
        clientes[websocket] = usuario_id
        usuario_canal[websocket] = canal_general_id
        db_manager.cambiar_estado_usuario(usuario_id, True)

        # ENVIAR BIENVENIDA
        await websocket.send(json.dumps({
            "tipo": "bienvenida",
            "mensaje": f"Bienvenido {usuario['nombre']}",
            "usuario": usuario["nombre"]
        }))

        # NOTIFICAR A TODOS
        await broadcast(
            canal_general_id,
            json.dumps({
                "tipo": "usuario_conectado",
                "usuario": usuario["nombre"]
            })
        )

        # ================================
        # 4. LOOP PRINCIPAL
        # ================================
        while True:
            raw_msg = await websocket.recv()
            try:
                data = json.loads(raw_msg)
            except json.JSONDecodeError:
                # Mensaje no JSON → enviamos error JSON
                await websocket.send(json.dumps({
                    "tipo": "error",
                    "mensaje": "Mensaje no JSON recibido"
                }))
                continue

            contenido = data.get("contenido", "")
            tipo = data.get("tipo", "mensaje")

            # COMANDOS
            if tipo == "comando":
                if await procesar_comando(websocket, usuario_id, contenido):
                    continue

            # MENSAJES NORMALES
            canal_id = usuario_canal.get(websocket, canal_general_id)
            
            # 1. Calcular hash SHA-256 para auditoría
            hash_sha256 = calcular_hash_sha256(contenido)

            # 2. Guardar mensaje en DB
            db_manager.guardar_mensaje(usuario_id, canal_id, contenido, hash_sha256)

            # 3. Escribir log de auditoría
            escribir_log_auditoria(usuario["nombre"], contenido, hash_sha256)

            # 4. Crear HMAC opcional si quieres integridad adicional
            hmac_mensaje = crear_hmac(contenido.encode())
            
            canales = db_manager.obtener_canales_donde_estoy(usuario_id)

            # ENVIAR JSON A TODOS
            await broadcast(
                canal_id,
                json.dumps({
                    "tipo": "mensaje",
                    "usuario": usuario["nombre"],
                    "contenido": contenido,
                    "fecha": data.get("fecha", datetime.utcnow().isoformat()),
                     "hmac": hmac_mensaje,
                     "lista":canales
                })
            )

    except Exception as e:
        print(f"Cliente desconectado ({usuario['nombre']}): {e}")

    finally:
        # ================================
        # 5. DESCONEXIÓN
        # ================================
        if websocket in clientes:
            del clientes[websocket]
        if websocket in usuario_canal:
            del usuario_canal[websocket]

        db_manager.cambiar_estado_usuario(usuario_id, False)

        await broadcast(
            canal_general_id,
            json.dumps({
                "tipo": "usuario_desconectado",
                "usuario": usuario["nombre"]
            })
        )