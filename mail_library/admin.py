from django.contrib import admin
from .models import MessageHistory, Message, UserProfile


class MessageHistoryInline(admin.TabularInline):
    model = MessageHistory
    extra = 0
    fields = ('time',
              'get_color_event',
              'failed_status',
              'delivery_code',
              'delivery_message')
    readonly_fields = ('time',
                       'get_color_event',
                       'failed_status',
                       'delivery_code',
                       'delivery_message')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    fields = ('message_id',
              'to',
              'subject',
              'url',
              'key')
    readonly_fields = ('message_id',
                       'to',
                       'subject',
                       'url',
                       'key')
    list_display = ('message_id', 'last_event',)
    inlines = [MessageHistoryInline, ]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    pass
