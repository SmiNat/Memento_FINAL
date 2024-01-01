from django.contrib import admin

from .models import Profile, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["username", "date_joined"]
    list_display = ["username", "email", "date_joined", "is_active", "is_staff"]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    exclude = []
    ordering = ["created"]
    list_display = ["username", "email", "created"]
