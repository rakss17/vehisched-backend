from django.contrib import admin
from .models import Request, Type, Vehicle_Driver_Status, Question, Answer, AddressFromGoogleMap

admin.site.register(Request)
admin.site.register(Type)
admin.site.register(Vehicle_Driver_Status)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(AddressFromGoogleMap)