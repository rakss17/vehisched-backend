# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Vehicle
from .serializers import VehicleSerializer
import logging
from asgiref.sync import sync_to_async
import asyncio
from django.core.files.uploadedfile import InMemoryUploadedFile

logger = logging.getLogger(__name__)


class VehicleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            await self.accept()
        except Exception as e:
            logger.exception("WebSocket connection failed: %s", str(e))

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        print(data)

        if action == 'post_vehicle':
            await self.post_vehicle(data)
        elif action == 'fetch_vehicles':
            await self.fetch_vehicles()
        elif action == 'update_vehicle':
            await self.update_vehicle(data)

    async def post_vehicle(self, data):
        uploaded_file_data = data['data'].pop('vehicle_image', None)
        print("image data: ", uploaded_file_data)

        serializer = VehicleSerializer(data=data['data'])

        is_valid = await sync_to_async(serializer.is_valid)()

        if is_valid:
            vehicle = await sync_to_async(serializer.save)()

            # Handle the file data and save it to the model's vehicle_image field
            if uploaded_file_data:
                # Convert the binary data back into a file
                # This is a simplified example and may not work for all file types and situations
                uploaded_file = io.BytesIO(uploaded_file_data)
                uploaded_file.name = 'uploaded_file.png'

                # Save the uploaded file to the model
                vehicle.vehicle_image.save(uploaded_file.name, uploaded_file)
                vehicle.save()

            response_data = {
                'action': 'vehicle_posted',
                'data': VehicleSerializer(vehicle).data
            }
        else:
            response_data = {
                'action': 'vehicle_post_error',
                'errors': serializer.errors
            }

        # Use self.send() to send JSON data
        await self.send(json.dumps(response_data))

    async def fetch_vehicles(self):
        vehicles = await sync_to_async(list)(Vehicle.objects.all())
        serializer = await sync_to_async(VehicleSerializer)(vehicles, many=True)
        serialized_vehicles = serializer.data
        response_data = {
            'action': 'vehicles_fetched',
            'data': serialized_vehicles
        }
        await self.send(text_data=json.dumps(response_data))

    async def update_vehicle(self, data):
        vehicle = Vehicle.objects.get(pk=data.get('pk'))
        serializer = VehicleSerializer(vehicle, data=data, partial=True)

        if serializer.is_valid():
            updated_vehicle = serializer.save()
            response_data = {
                'action': 'vehicle_updated',
                'data': VehicleSerializer(updated_vehicle).data
            }
        else:
            response_data = {
                'action': 'vehicle_update_error',
                'errors': serializer.errors
            }

        await self.send(text_data=json.dumps(response_data))

    async def disconnect(self, close_code):
        pass
