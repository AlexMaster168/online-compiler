from django.contrib import admin

from .models import Execution, Snippet


@admin.register(Snippet)
class SnippetAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "language", "owner", "forked_from", "views", "updated_at")
    list_filter = ("language",)
    search_fields = ("id", "title", "code", "owner__username")
    readonly_fields = ("id", "views", "session_key", "created_at", "updated_at")
    raw_id_fields = ("owner", "forked_from")


@admin.register(Execution)
class ExecutionAdmin(admin.ModelAdmin):
    list_display = ("id", "language", "status", "user", "backend", "time_ms", "memory_kb", "client_ip", "created_at")
    list_filter = ("status", "language", "backend")
    search_fields = ("code", "stdout", "stderr")
    date_hierarchy = "created_at"
    readonly_fields = [f.name for f in Execution._meta.fields]

    def has_add_permission(self, request):
        return False
