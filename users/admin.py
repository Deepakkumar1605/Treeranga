from django.contrib import admin

from . import models

@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ("id",)
    list_display = ("id","email")
