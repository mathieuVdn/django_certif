import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ImportProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("import_progress", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("import_progress", self.channel_name)

    async def update_status(self, event):
        status = event.get("status")
        # Envoyer la nouvelle valeur du statut au client
        await self.send(text_data=json.dumps({"status": status}))
