from django.contrib import admin
from .models import Request, Type, Vehicle_Driver_Status, CSM, Question, Answer

admin.site.register(Request)
admin.site.register(Type)
admin.site.register(Vehicle_Driver_Status)
admin.site.register(CSM)
admin.site.register(Question)
admin.site.register(Answer)