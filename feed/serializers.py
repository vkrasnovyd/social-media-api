from rest_framework import serializers

from feed.models import Hashtag


class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ("id", "name")
