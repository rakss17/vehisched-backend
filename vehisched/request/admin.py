from django.contrib import admin
from .models import Request, Request_Status, Category, Sub_Category

admin.site.register(Request)
admin.site.register(Request_Status)
admin.site.register(Category)
admin.site.register(Sub_Category)