from realtimelinks.twitlinks.models import Link, Hit
from django.contrib import admin

class LinkAdmin(admin.ModelAdmin):
    list_display = ['short_url' , 'occurrences', 'last_seen', 'long_url', 'title']

class HitAdmin(admin.ModelAdmin):
    list_display = ['pk' , 'at', 'link']

admin.site.register(Link, LinkAdmin)
admin.site.register(Hit, HitAdmin)
