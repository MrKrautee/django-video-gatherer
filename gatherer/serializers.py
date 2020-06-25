from rest_framework import serializers
from gatherer.models import Video, Tag, TagContent, YtChannel, FbSite



class TagContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = TagContent
        fields = ['language', 'name', 'description', 'slug', 'id']

class TagSerializer(serializers.ModelSerializer):

    content = TagContentSerializer(source='tagcontent_set', many=True, read_only=True)
    class Meta:
        model = Tag
        fields = ['content']


class YtChannelSerializer(serializers.ModelSerializer):

    class Meta:
        model = YtChannel
        fields = ['title', 'description']


class FbSiteSerializer(serializers.ModelSerializer):

    class Meta:
        model = FbSite
        fields = ['slug', 'url']

class VideoSerializer(serializers.ModelSerializer):

    publisher = serializers.StringRelatedField(many=False)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Video
        tags = serializers.ReadOnlyField(source='tags')
        fields = ['title', 'description', 'image', 'duration', 'published_at',
                  'tags', 'language', 'link', 'publisher', 'type']
        #? child, publisher, link, 
