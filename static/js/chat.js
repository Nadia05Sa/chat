/* ===========================================
   RESPONSIVE MENU
=========================================== */
window.addEventListener("resize", () => {
    if (window.innerWidth > 768) document.body.classList.remove("show");
});

let canal = null;

let my_name = "";

let my_email = "";

const perfilImg = document.getElementById("side_img");

function setCanalName() {
    const chat = document.getElementById("chat_name");
    chat.innerHTML = '';
    chat.innerHTML = canal.nombre
    const img = document.getElementById("img_contact")
    img.src = `https://avatar.iran.liara.run/username?username=${canal.nombre}`
}

/* Cierra el menú cuando está en modo móvil */
function closeMenu() {
    if (window.innerWidth < 768) {
        document.body.classList.remove("show");
    }
}

/* Cierra menú (si móvil) y cambia modo oscuro */
function closeAndToggle() {
    if (window.innerWidth < 768) {
        document.body.classList.remove("show");
    }
    document.body.classList.toggle("dark");
}

const comandos = ["/crear", "/crear_priv", "/unir", "/salir"];

const comands = [
    { comando: "/crear nombre", descripcion: "Crear canal público" },
    { comando: "/crear_priv nombre", descripcion: "Crear canal privado" },
    { comando: "/unir nombre", descripcion: "Unirse a un canal" },
    { comando: "/salir", descripcion: "Volver al canal general" },
    { comando: "/agregar email canal", descripcion: "Agregar usuario a canal (solo admin)" },
    { comando: "/remover email canal", descripcion: "Remover usuario de canal (solo admin)" },
    { comando: "/dar_admin email canal", descripcion: "Dar permisos de admin (solo admin)" },
    { comando: "/quitar_admin email canal", descripcion: "Quitar permisos de admin (solo admin)" }
];

// Ejemplo: imprimir en consola
comandos.forEach(c => console.log(`${c.comando} → ${c.descripcion}`));


/* ===========================================
   CONFIG CLIENTE (USUARIO)
=========================================== */
const WS_URL = "ws://localhost:5001";

let socket = null;
let reconectando = false;

/* ID generado o recuperado */
let usuarioActual = {
    _id: sessionStorage.getItem("user_id") || null,
    google_id: sessionStorage.getItem("user_google_id") || null
};

/* Guardar ID si no existía */
sessionStorage.setItem("user_id", usuarioActual._id);

/* ===========================================
   CONEXIÓN WEBSOCKET
=========================================== */
function conectarWS() {
    console.log("[WS] Conectando a", WS_URL);

    socket = new WebSocket(WS_URL);

    /* Cuando conecta */
    socket.onopen = () => {
        console.log("🟢 WebSocket conectado");

        const payload = {
            usuario_id: usuarioActual._id,
            google_id: usuarioActual.google_id ?? null
        };

        socket.send(JSON.stringify(payload));
    };

    /* Cuando recibe un mensaje */
    socket.onmessage = (event) => {
        let data;

        try {
            data = JSON.parse(event.data);
        } catch {
            console.warn("Mensaje no JSON:", event.data);
            return;
        }

        console.log("📩 MSG:", data);

        switch (data.tipo) {
            case "mensaje":
                renderCanalesSocket(data.lista);
                agregarMensajeAlDOM(data);
                break;

            case "historial":
                // Muestra primero mensaje de sistema al unirse al canal
                if (data.contenido) {
                    agregarMensajeSistema({ texto: data.contenido });
                }
                // Si viene información de canal (al unir)
                if (data.canal) {
                    canal = data.canal;
                    setCanalName();
                }

                if (data.mensajes.length === 0) {
                    paintMessageEmpty();
                } else {
                    renderHistorial(data.mensajes);
                }
                break;

            case "comando":
                switch (data.comando) {
                    case "/crear":
                    case "/crear_priv":
                        renderCanalesSocket(data.lista);
                        break;
                }
                agregarMensajeSistema({ texto: data.resultado.mensaje ?? data.mensaje ?? data.resultado });
                break;
            case "bienvenida":
                agregarMensajeSistema({ texto: data.resultado ?? data.mensaje });
                break;

            case "usuario_conectado":
            case "usuario_desconectado":
                agregarMensajeSistema({ texto: `${data.usuario} se ha ${data.tipo === "usuario_conectado" ? "conectado" : "desconectado"}` });
                break;

            default:
                console.warn("Tipo desconocido:", data.tipo);
        }
    };

    /* Cuando se desconecta */
    socket.onclose = () => {
        console.warn("🔴 WS cerrado");

        if (!reconectando) {
            reconectando = true;
            console.log("⏳ Reintentando WS en 2s...");
            setTimeout(() => {
                reconectando = false;
                conectarWS();
            }, 2000);
        }
    };

    /* Cuando hay error */
    socket.onerror = (err) => console.error("⚠ WS Error:", err);
}

/* ===========================================
   ENVIAR MENSAJE
=========================================== */
function enviarMensaje(texto) {
    if (!texto.trim()) return;

    if (!socket || socket.readyState !== WebSocket.OPEN) {
        console.warn("WS no conectado aún");
        return;
    }

    const esComando = comandos.some(cmd => texto.trim().startsWith(cmd));

    const msg = {
        tipo: esComando ? "comando" : "mensaje",
        usuario_id: usuarioActual._id,
        google_id: usuarioActual.google_id,
        contenido: texto,
        fecha: new Date().toISOString(),
    };

    socket.send(JSON.stringify(msg));

    // limpiar textarea
    document.getElementById("mensaje").value = "";
}

/* ===========================================
   AGREGAR MENSAJES AL DOM
=========================================== */
function agregarMensajeAlDOM(data) {
    const chat = document.getElementById("chat");
    const div = document.createElement("div");

    // Si viene información de canal (al unir)
    if (data.canal) {
        canal = data.canal;
        setCanalName();
    }

    const gottenName = data.nombre ?? data.usuario

    if (gottenName?.trim().toLowerCase() === my_name?.trim().toLowerCase()) {
        div.innerHTML = `<div> ${data.contenido ?? data.texto}<p>${formatearFecha(data.fecha)}</p></div>`;
        div.classList.add("my-message");
    } else {
        div.classList.add("them-message");
        div.innerHTML = `<div>
        <strong>${data.nombre ?? data.usuario}:</strong> ${data.contenido ?? data.texto}
        <p>${formatearFecha(data.fecha)}</p>
        </div>`;
    }
    // Mensaje normal
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

function agregarMensajeSistema(data) {
    const chat = document.getElementById("chat");
    const div = document.createElement("div");

    div.classList.add("system-message");
    div.innerHTML = `<em>${data.texto ?? data.resultado}</em>`;

    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

/* ===========================================
   RENDER DE USUARIOS O CANALES
=========================================== */
let showGroups = true

const toggleShow = () => showGroups = !showGroups;

async function renderUsuarios() {
    const ul = document.getElementById("lista-usuarios");
    ul.innerHTML = "";

    let lista = [];

    try {
        const res = await fetch("/usuarios", {
            headers: { "Content-Type": "application/json" },
        });
        const data = await res.json();
        if (!res.ok) return alert(data.error);

        lista = data;
    } catch (err) {
        alert("Error al obtener usuarios: " + err);
    }

    lista.forEach((u) => {
        if (u._id === usuarioActual._id) return; // no mostrarte a ti mismo

        ul.insertAdjacentHTML(
            "beforeend",
            `
            <li class="user-item ${u.activo ? "active" : ""}" data-id="${u._id}">
                <img src="${u.picture ?? `https://avatar.iran.liara.run/username?username=${u.nombre}+${u.apellido ?? ""}`}">
                
                <div class="user-item-data">
                    <div class="user-item-div">
                        <h5 class="user-item-name">${u.nombre}</h5>
                        <p class="user-item-time">${formatearFecha(u.ultima_conexion) || ""}</p>
                    </div>

                    <div class="user-item-div">
                        <h6 class="user-item-mensaje">${u.ultimo || ""}</h6>
                    </div>
                </div>
            </li>
            `
        );
    });
}

async function renderCanales() {
    const ul = document.getElementById("lista-usuarios");
    ul.innerHTML = "";

    let lista = [];

    try {
        const res = await fetch(`/canales/${usuarioActual._id}`, {
            headers: { "Content-Type": "application/json" },
        });
        const data = await res.json();
        if (!res.ok) return alert(data.error);

        lista = data;
    } catch (err) {
        alert("Error al obtener canales: " + err);
        return;
    }

    lista.forEach((u) => {
        const mostrarUsuario =
            u.ultimo?.usuario_nombre && u.ultimo.usuario_nombre !== my_name
                ? `<strong>${u.ultimo.usuario_nombre}:</strong> `
                : "";
        const li = document.createElement("li");
        li.className = `user-item ${canal?._id === u._id ? "active" : ""}`;

        li.innerHTML = `
            <img src="${u.picture ?? `https://avatar.iran.liara.run/username?username=${u.nombre}`}">
            <div class="user-item-data">
                <div class="user-item-div">
                    <h5 class="user-item-name">${u.nombre}</h5>
                    <p class="user-item-time">Creado: ${formatearFecha(u.fecha_creacion) || ""}</p>
                </div>
                <div class="user-item-div">
                    <h6 class="user-item-mensaje">${mostrarUsuario} ${u.ultimo?.contenido ?? "Sin mensajes"}</h6>
                </div>
            </div>
        `;

        // Listener seguro que pasa el objeto completo
        li.addEventListener("click", () => { joinCanal(u); closeMenu() });

        ul.appendChild(li);
    });
}

async function renderCanalesSocket(lista) {
    const ul = document.getElementById("lista-usuarios");
    ul.innerHTML = "";

    lista.forEach((u) => {
        const mostrarUsuario =
            u.ultimo?.usuario && u.ultimo.usuario !== my_name
                ? `<strong>${u.ultimo.usuario}:</strong> `
                : "";
        const li = document.createElement("li");
        li.className = `user-item ${canal?._id === u._id ? "active" : ""}`;

        li.innerHTML = `
            <img src="${u.picture ?? `https://avatar.iran.liara.run/username?username=${u.nombre}`}">
            <div class="user-item-data">
                <div class="user-item-div">
                    <h5 class="user-item-name">${u.nombre}</h5>
                    <p class="user-item-time">Creado: ${formatearFecha(u.fecha_creacion) || ""}</p>
                </div>
                <div class="user-item-div">
                    <h6 class="user-item-mensaje">${mostrarUsuario} ${u.ultimo?.contenido ?? "Sin mensajes"}</h6>
                </div>
            </div>
        `;

        // Listener seguro que pasa el objeto completo
        li.addEventListener("click", () => { joinCanal(u); closeMenu() });

        ul.appendChild(li);
    });
}

function joinCanal(canalObj) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        console.warn("WS no conectado aún");
        return;
    }

    canal = canalObj; // actualizar canal actual
    setCanalName();   // actualizar UI

    const msg = {
        tipo: "comando",
        usuario_id: usuarioActual._id,
        nombre: usuarioActual.nombre,
        contenido: `/unir ${canal.nombre}`,
        fecha: new Date().toISOString(),
    };

    socket.send(JSON.stringify(msg));
}

/* ===========================================
   MOSTRARLE COMANDOS AL USUARIO
=========================================== */
const showCommands = () => {
    comandos.forEach(c => {
        const chat = document.getElementById("chat");
        const div = document.createElement("div");

        div.classList.add("mensaje");
        div.innerHTML = `<strong>${c}:</strong> `;

        chat.appendChild(div);
        chat.scrollTop = chat.scrollHeight;
    });
}

/* ===========================================
   CARGAR HISTORIAL DE MENSAJES
=========================================== */
function renderHistorial(mensajes) {
    const chat = document.getElementById("chat");
    chat.innerHTML = ""; // Limpiar chat actual

    mensajes.forEach(m => {
        agregarMensajeAlDOM({
            nombre: m.usuario ?? m.nombre,
            contenido: m.contenido,
            fecha: m.fecha
        });
    });
}

/* ===========================================
   ENVIAR MENSAJE (BOTÓN)
=========================================== */
document.getElementById("send").addEventListener("click", () => {
    enviarMensaje(document.getElementById("mensaje").value);
});

/* Enter para enviar */
document.getElementById("mensaje").addEventListener("keypress", e => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        enviarMensaje(e.target.value);
    }
});

/* ===========================================
   AUTO-LOAD
=========================================== */
window.onload = () => {
    validarUsuario();
};

/* ===========================================
   CONSUMO DE ENDPOINT /perfil
=========================================== */
async function cargarPerfil() {
    const id = usuarioActual._id;

    try {
        const res = await fetch(`/perfil/${id}`);
        const data = await res.json();

        if (!res.ok) {
            console.warn("Error perfil:", data.error);
            return;
        }

        my_name = data.nombre;
        my_email = data.email;
        perfilImg.src = data.picture ?? `https://avatar.iran.liara.run/username?username=${data.nombre}+${data.apellido ?? ''}`
    } catch (err) {
        console.error("Error obteniendo perfil:", err);
    }
}

//Formatear fecha
function formatearFecha(fechaStr) {
    const dt = new Date(fechaStr); // procesa Tue, 18 Nov 2025 00:44:23 GMT
    const ahora = new Date();

    const esHoy =
        dt.getFullYear() === ahora.getFullYear() &&
        dt.getMonth() === ahora.getMonth() &&
        dt.getDate() === ahora.getDate();

    if (esHoy) {
        // Solo la hora
        return dt.toLocaleTimeString("es-MX", {
            hour: "2-digit",
            minute: "2-digit",
        });
    } else {
        return dt.toLocaleString("es-MX", {
            day: "2-digit",
            month: "short",
            hour: "2-digit",
            minute: "2-digit",
        });
    }
}

async function validarUsuario() {
    const id = sessionStorage.getItem("user_id");

    if (!id || id === "null" || id === "undefined") {
        try {
            const res = await fetch("/session_user");
            const data = await res.json();
            if (data.logged) {
                sessionStorage.setItem("user_id", data.user._id);
                sessionStorage.setItem("user_google_id", data.user.google_id);
                conectarWS();
                cargarPerfil();
                renderCanales();
                return;
            } else {
                window.location.href = "/denied";
                window.history.replaceState({}, "", "/denied");
            }
        } catch (e) {
            console.error(e)
            window.location.href = "/denied";
            window.history.replaceState({}, "", "/denied");
        }
    } else {
        conectarWS();
        cargarPerfil();
        renderCanales();
        return;
    }
}

/* ===========================================
   COLOREAR LOS LORD-ICON
=========================================== */
document.addEventListener("DOMContentLoaded", () => {
    const icons = document.querySelectorAll("lord-icon");

    const cssPrimary = getComputedStyle(document.documentElement)
        .getPropertyValue("--primario").trim();

    const cssSecondary = getComputedStyle(document.documentElement)
        .getPropertyValue("--secundario").trim();

    icons.forEach(icon => {
        icon.setAttribute(
            "colors",
            `primary:${cssPrimary},secondary:${cssSecondary}`
        );
    });
});

const emmbeddMessage = `         
         <div class="lord_icon_chat">
            <lord-icon
                src="https://cdn.lordicon.com/tsrgicte.json"
                trigger="hover"
                style="width: 250px; height: 250px"
            >
            </lord-icon>
            <h2>¡Es hora de romper el hielo!</h2>
            <h4>
              Está conversación esta vacía, envía un mensaje para comenzar
            </h4>
          </div>`

function paintMessageEmpty() {
    const chat = document.getElementById("chat");
    chat.innerHTML = '';
    chat.innerHTML = emmbeddMessage;
}