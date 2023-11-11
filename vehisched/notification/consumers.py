import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationCreatedCanceledConsumer(AsyncWebsocketConsumer):
    async def connect(self):
       
        await self.accept()
        await self.channel_layer.group_add("notifications", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("notifications", self.channel_name)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'created':
            await self.notify_request_created({
                'message': 'Notification message goes here for created' 
            })
        elif action == 'completed':
            await self.notify_request_completed({
                'message': 'Notification message goes here for created' 
            })
        elif action == 'canceled':
            await self.notify_request_canceled({
                'message': 'Notification message goes here for canceled' 
            })


    async def notify_request_created(self, event):
    
        message = event["message"]
        await self.send(text_data=json.dumps({"type": "notify.request_created",
            "message": message, 'status': 'Created'}))
        
    async def notify_request_completed(self, event):
    
        message = event["message"]
        await self.send(text_data=json.dumps({"type": "notify.request_completed",
            "message": message, 'status': 'Completed'}))
        
    async def notify_request_canceled(self, event):
    
        message = event["message"]
        await self.send(text_data=json.dumps({"type": "notify.request_canceled",
            "message": message,}))


class NotificationApprovalScheduleReminderConsumer(AsyncWebsocketConsumer):
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
        elif action == "reminder":
            await self.schedule_reminder({
                'message': "Notification message goes here"
            })
        elif action == 'reject':
            await self.approve_notification({
                'message': 'Notification message goes here' 
            })
           
    async def reject_notification(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({'type': 'reject.notification','message': message, 'status': 'Rejected'}))
        
    async def approve_notification(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({'type': 'approve.notification','message': message, 'status': 'Approved'}))

    async def schedule_reminder(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({'type': 'schedule.reminder', 'message': message}))