import json

from channels.generic.websocket import AsyncWebsocketConsumer

from .realtime import WORKFLOW_GROUP


class ClinicFlowConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope.get("user") or self.scope["user"].is_anonymous:
            await self.close()
            return

        await self.channel_layer.group_add(WORKFLOW_GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(WORKFLOW_GROUP, self.channel_name)

    async def workflow_event(self, event):
        await self.send(text_data=json.dumps(event["payload"]))
