class ConnectionManager:
    def __init__(self):
        self.usuarios = {}  # usuario_id → websocket

    async def conectar(self, usuario_id, websocket):
        await websocket.accept()
        self.usuarios[usuario_id] = websocket

    def desconectar(self, usuario_id):
        if usuario_id in self.usuarios:
            del self.usuarios[usuario_id]

    async def enviar_a_usuario(self, usuario_id, data):
        if usuario_id in self.usuarios:
            await self.usuarios[usuario_id].send_json(data)

    async def broadcast(self, data):
        for ws in self.usuarios.values():
            await ws.send_json(data)

manager = ConnectionManager()
