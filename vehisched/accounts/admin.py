from django.contrib import admin
from .models import User, Role, Driver_Status, Office

admin.site.register(User)
admin.site.register(Role)
admin.site.register(Driver_Status)
admin.site.register(Office)
