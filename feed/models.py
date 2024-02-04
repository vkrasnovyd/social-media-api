import os
import uuid

from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Hashtag(models.Model):
    name = models.CharField(
        max_length=50,
        unique=False,
        validators=[
            RegexValidator(
                regex="^[\w]*$",
                message="Hashtag doesnt comply",
            )
        ],
    )

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
    hashtags = models.ManyToManyField(
        Hashtag, related_name="posts", blank=True
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Post created by {self.author} at {self.created_at}"

    def get_absolute_url(self):
        return reverse("feed:post-detail", kwargs={"pk": self.pk})


def post_image_file_path(instance, filename) -> str:
    _, extension = filename.split(".")

    filename = (
        f"{slugify(instance.post.author.username)}_"
        f"{instance.post.created_at.strftime('%Y-%m-%d_%H-%M-%S')}-"
        f"{uuid.uuid4()}.{extension}"
    )

    return os.path.join("uploads/posts/", filename)


class PostImage(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(
        blank=False, null=False, upload_to=post_image_file_path
    )


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
