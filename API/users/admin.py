from django.contrib import admin

from .models import Item, UserProfile


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "user", "created_at")
    search_fields = ("name", "description")
    list_filter = ("status", "category", "location")
    ordering = ("-created_at",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "profile_picture", "is_banned")
    search_fields = ("user__email", "user__first_name")
    list_filter = ("user__is_active", "user__is_staff", "is_banned")
    ordering = ("id",)
    list_editable = ("is_banned",)
