# Generated by Django 5.0.1 on 2024-02-12 17:36

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("feed", "0005_alter_hashtag_name"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="post",
            options={"ordering": ("-published_at",)},
        ),
        migrations.AddField(
            model_name="post",
            name="is_published",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="post",
            name="published_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
