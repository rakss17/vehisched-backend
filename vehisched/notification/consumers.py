import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
       
        await self.accept()
        await self.channel_layer.group_add("notifications", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("notifications", self.channel_name)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        print(action)

        if action == 'created':
            await self.notify_request_created({
                'message': 'Notification message goes here for created' 
            })
        elif action == 'canceled':
            await self.notify_request_canceled({
                'message': 'Notification message goes here for canceled' 
            })


    async def notify_request_created(self, event):
    
        message = event["message"]
        await self.send(text_data=json.dumps({"type": "notify.request_created",
            "message": message,}))
        
    async def notify_request_canceled(self, event):
    
        message = event["message"]
        await self.send(text_data=json.dumps({"type": "notify.request_canceled",
            "message": message,}))
