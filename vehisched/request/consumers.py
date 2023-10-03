# consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
from .models import Request
from django.utils import timezone



class RequestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        
        await self.accept()
        requester_name = self.scope.get('query_string').decode('utf-8').split('=')[1]
        await self.channel_layer.group_add(f"user_{requester_name}", self.channel_name)

    async def disconnect(self, close_code):
        requester_name = self.scope.get('query_string').decode('utf-8').split('=')[1]
        await self.channel_layer.group_discard(f"user_{requester_name}", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'approve':
            await self.approve_notification({
                'message': 'Notification message goes here' 
            })

    async def approve_notification(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({'type': 'approve.notification','message': message, 'status': 'Approved'}))
