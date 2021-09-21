from rest_framework import serializers
from django.utils.timesince import timesince
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy 
from gatherer.models import Video, Tag, TagContent, YtChannel, FbSite


def truncate(text: str, chars_count: int) -> str:
    """ truncate text after chars_count, but cut
        at the previous ocurrig blank.
    """
    if len(text) <= chars_count:
        return text
    idx_to_cut = None
    if text[chars_count] == ' ':
        idx_to_cut = chars_count
    else:
        for idx in range(chars_count, -1, -1):
            if text[idx] == ' ':
                idx_to_cut = idx
                break
        # no blank in text
        if not idx_to_cut:
            idx_to_cut = chars_count

    return f"{text[0:idx_to_cut]} ..."


class TagContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = TagContent
        fields = ['language', 'name', 'description', 'slug', 'id']


class TagSerializer(serializers.ModelSerializer):

    content = TagContentSerializer(source='tagcontent_set',
                                   many=True, read_only=True)

    class Meta:
        model = Tag
        fields = ['content']


class TranslatedTagSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['name', 'slug']

    def get_name(self, obj):
        try:
            return obj.name(self.context['request'].LANGUAGE_CODE)
        except KeyError:
            print("glitch: no lang code")
            return obj.name('en') #@HACK

    def get_slug(self, obj):
        try:
            return obj.slug(self.context['request'].LANGUAGE_CODE)
        except KeyError:
            return obj.name('en') #@HACK
        


class YtChannelSerializer(serializers.ModelSerializer):

    class Meta:
        model = YtChannel
        fields = ['title', 'description']


class FbSiteSerializer(serializers.ModelSerializer):

    class Meta:
        model = FbSite
        fields = ['slug', 'url']


TIME_STRINGS = {
    'year': ngettext_lazy('%d year', '%d years'),
    'month': ngettext_lazy('%d month', '%d months'),
    'week': ngettext_lazy('%d week', '%d weeks'),
    'day': ngettext_lazy('%d day', '%d days'),
    'hour': ngettext_lazy('%d hour', '%d hours'),
    'minute': ngettext_lazy('%d minute', '%d minutes'),
}
class VideoSerializer(serializers.ModelSerializer):

    publisher = serializers.SerializerMethodField()
    tags = TranslatedTagSerializer(many=True, read_only=True)
    # tags = TagSerializer(many=True, read_only=True)
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    published_at = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    # ? child, publisher, link

    class Meta:
        model = Video
        tags = serializers.ReadOnlyField(source='tags')
        fields = ['title', 'description', 'image', 'duration', 'published_at',
                  'tags', 'language', 'link', 'publisher', 'type']

    def get_title(self, obj):
        return truncate(obj.title, 85)

    def get_description(self, obj):
        return truncate(obj.description, 240)

    def get_publisher(self, obj):
        return truncate(str(obj.publisher), 35)

    def get_published_at(self, obj):
        return _("%s ago") % timesince(obj.published_at,
                                       time_strings=TIME_STRINGS)

    def get_type(self, obj):
        type = obj.type.replace("video", "")
        return type.capitalize()
