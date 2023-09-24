from django.contrib import admin
from .models import Request, Request_Status

admin.site.register(Request)
admin.site.register(Request_Status)
