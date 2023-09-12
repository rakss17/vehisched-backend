# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Vehicle
from .serializers import VehicleSerializer
import logging

logger = logging.getLogger(__name__)


class VehicleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            await self.accept()
        except Exception as e:
            logger.exception("WebSocket connection failed: %s", str(e))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'post_vehicle':
            await self.post_vehicle(data)
        elif action == 'fetch_vehicles':
            await self.fetch_vehicles()
        elif action == 'update_vehicle':
            await self.update_vehicle(data)

    async def post_vehicle(self, data):
        serializer = VehicleSerializer(data=data)

        if serializer.is_valid():
            vehicle = serializer.save()
            response_data = {
                'action': 'vehicle_posted',
                'data': VehicleSerializer(vehicle).data
            }
        else:
            response_data = {
                'action': 'vehicle_post_error',
                'errors': serializer.errors
            }

        await self.send(text_data=json.dumps(response_data))

    async def fetch_vehicles(self):
        vehicles = Vehicle.objects.all()
        serialized_vehicles = VehicleSerializer(vehicles, many=True).data
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
