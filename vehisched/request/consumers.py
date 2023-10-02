# consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
from .models import Request
from django.utils import timezone


class RequestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Authenticate the user here if necessary
        await self.accept()
        await self.channel_layer.group_add("request_status_approved", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("request_status_approved", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'approve':
            await self.approve_notification({
                'message': 'Notification message goes here' 
            })
    async def approve_notification(self, event):
        # Send a notification to the owner of the request when it's approved
        message = event['message']
        await self.send(text_data=json.dumps({'type': 'approve.notification','message': message}))
