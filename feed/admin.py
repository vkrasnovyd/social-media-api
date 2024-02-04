from django.contrib import admin

from feed.models import Hashtag, Post, Comment, Like

admin.site.register(Hashtag)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Like)
