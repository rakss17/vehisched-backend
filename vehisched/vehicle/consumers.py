import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Vehicle
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async, async_to_sync
from django.core.exceptions import ObjectDoesNotExist

class VehicleStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("vehicle_status_updates", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("vehicle_status_updates", self.channel_name)
        
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'fetch_available_vehicles':
            await self.fetch_available_vehicles()

    async def fetch_available_vehicles(self):
        available_vehicles = await self.get_available_vehicles()
        await self.send(text_data=json.dumps({
            'type': 'available.vehicles',
            'data': available_vehicles,
        }))

    @sync_to_async
    def get_available_vehicles(self):
        available_vehicles = Vehicle.objects.filter(status__description='Available')
        vehicles_list = []

        for vehicle in available_vehicles:
            vehicles_list.append({
                'plate_number': vehicle.plate_number,
                'vehicle_name': vehicle.vehicle_name,
                'vehicle_type': vehicle.vehicle_type,
                'capacity': vehicle.capacity,
                'status': vehicle.status.description if vehicle.status else None,
                'is_vip': vehicle.is_vip,
                'vehicle_image': vehicle.vehicle_image.url if vehicle.vehicle_image else None,
                'created_at': vehicle.created_at.strftime('%Y-%m-%d %H:%M:%S') if vehicle.created_at else None,
            })



        return vehicles_list

    @sync_to_async
    def fetch_vehicle_data(self, plate_number):
        try:
            vehicle = Vehicle.objects.get(plate_number=plate_number)
            return {
                'plate_number': vehicle.plate_number,
                'vehicle_name': vehicle.vehicle_name,
                'vehicle_type': vehicle.vehicle_type,
                'capacity': vehicle.capacity,
                'status': vehicle.status.description if vehicle.status else None,
                'is_vip': vehicle.is_vip,
                'vehicle_image': vehicle.vehicle_image.url if vehicle.vehicle_image else None,
                'created_at': vehicle.created_at.strftime('%Y-%m-%d %H:%M:%S') if vehicle.created_at else None,
            }
        except ObjectDoesNotExist:
            return None

    async def status_update(self, event):
        plate_number = event["plate_number"]
        vehicle_data = await self.fetch_vehicle_data(plate_number)

        if vehicle_data is not None:
            await self.send(text_data=json.dumps({
                'type': 'status.update',
                'message': f"Vehicle {plate_number} {event['message']}",
                'data': vehicle_data,
            }))
        else:
            await self.send(text_data=json.dumps({
                'type': 'status.update',
                'message': f"Vehicle {plate_number} not found: {event['message']}",
            }))


