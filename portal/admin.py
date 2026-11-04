from django.contrib import admin
from .models import Server, SiteSettings, Entry
@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "address", "is_published", "status_online")
    list_filter = ("kind", "is_published")
    search_fields = ("name", "address")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("status_online", "status_checked_at", "players_online", "players_max", "reported_version")
    fieldsets = [
        ("Wizytówka", {"fields": ("name", "slug", "kind", "address", "description", "game_version", "join_instructions", "rules", "modpack_url", "is_published", "order")}),
        ("Status Minecraft Java", {"fields": ("status_enabled", "status_host", "status_port", "status_online", "status_checked_at", "players_online", "players_max", "reported_version")}),
    ]
@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "server", "is_published", "published_at")
    list_filter = ("kind", "is_published")
    search_fields = ("title", "body")
    prepopulated_fields = {"slug": ("title",)}
@admin.register(SiteSettings)
class SettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists() and super().has_add_permission(request)
    def has_delete_permission(self, request, obj=None):
        return False
admin.site.site_header = "Minecraft Community CMS"
admin.site.site_title = "Panel społeczności"
admin.site.index_title = "Treści i serwery"
