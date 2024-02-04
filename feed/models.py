from django.contrib.auth import get_user_model
from django.db import models


class Hashtag(models.Model):
    name = models.CharField(max_length=31)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Post(models.Model):
    author = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="posts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
    hashtags = models.ManyToManyField(Hashtag, related_name="posts")

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Post created by {self.author} at {self.created_at}"


class Comment(models.Model):
    author = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="comments"
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField()

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"Comment left by {self.author} to {self.post.author}'s post"


class Like(models.Model):
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="likes"
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="likes"
    )

    class Meta:
        ordering = ("user__first_name", "user__last_name")
        unique_together = ("user", "post")
