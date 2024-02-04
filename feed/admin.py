from django.contrib import admin

from feed.models import Hashtag, Post, Comment, Like, PostImage


class ImageInline(admin.StackedInline):
    model = PostImage
    extra = 1


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    inlines = (ImageInline,)


admin.site.register(Hashtag)
admin.site.register(Comment)
admin.site.register(Like)
