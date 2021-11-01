import logging

from django.utils.timesince import timesince
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from rest_framework import serializers
from gatherer.models import Tag, TagContent
from gatherer.models import Video, YtChannel
from gatherer.models import Group, GroupContent

_logger = logging.getLogger(__name__)


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
            # _logger.error("glitch: no lang code")
            return obj.name('en')  # @HACK

    def get_slug(self, obj):
        try:
            return obj.slug(self.context['request'].LANGUAGE_CODE)
        except KeyError:
            # _logger.error("glitch: no lang code")
            return obj.name('en')  # @HACK


class GroupContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = GroupContent
        fields = ['language', 'name', 'description', 'id']
        order_by = ['name', ]


class GroupSerializer(serializers.ModelSerializer):

    content = GroupContentSerializer(source='groupcontent_set',
                                     many=True, read_only=True)

    class Meta:
        model = Group
        fields = ['content']


class TranslatedGroupSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ['name', 'tags']

    def get_name(self, obj):
        try:
            return obj.name(self.context['request'].LANGUAGE_CODE)
        except KeyError:
            # _logger.error("glitch: no lang code")
            return obj.name('en')  # @HACK

    def get_tags(self, obj):
        try:
            lang_code = self.context['request'].LANGUAGE_CODE
        except KeyError:
            lang_code = 'en'

        video_lang = self.context['video_lang']
        tag_filter = {
            'group_id': obj.id,
            'video__isnull': False,
            'video__language__in': video_lang,
            'video__is_active': True
        }
        tags = Tag.objects.filter(**tag_filter)
        tags = tags.distinct()
        tags = sorted(tags,
                      key=lambda tag: tag.name(lang_code))
        return TranslatedTagSerializer(tags, many=True,
                                       context=self.context).data


class YtChannelSerializer(serializers.ModelSerializer):

    class Meta:
        model = YtChannel
        fields = ['title', 'description']


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
        return obj.title

    def get_description(self, obj):
        return obj.description

    def get_publisher(self, obj):
        return str(obj.publisher)

    def get_published_at(self, obj):
        return _("%s ago") % timesince(obj.published_at,
                                       time_strings=TIME_STRINGS)

    def get_type(self, obj):
        type = obj.type.replace("video", "")
        return type.capitalize()


class TagPreviewSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()
    more = serializers.SerializerMethodField()

    videoManager = Video.objects.active()
    # @HACK:

    class Meta:
        model = Tag
        fields = ['name', 'slug', 'videos', 'more']

    def get_name(self, obj):
        try:
            return obj.name(self.context['request'].LANGUAGE_CODE)
        except KeyError:
            # _logger.error("glitch: no lang code")
            return obj.name('en')  # @HACK

    def get_slug(self, obj):
        try:
            return obj.slug(self.context['request'].LANGUAGE_CODE)
        except KeyError:
            # _logger.error("glitch: no lang code")
            return obj.name('en')  # @HACK

    def get_videos(self, obj):
        query = self.videoManager.filter(tags__id=obj.id)

        serializers = VideoSerializer(query[:6], many=True)
        return serializers.data

    def get_more(self, obj):
        return self.videoManager.filter(tags__id=obj.id).count() > 6
