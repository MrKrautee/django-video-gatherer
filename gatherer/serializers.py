from rest_framework import serializers
from rest_framework import filters
from django.conf import settings
from django.utils.timesince import timesince
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy 
from gatherer.models import Tag, TagContent
from gatherer.models import Video, YtChannel, FbSite
from gatherer.models import Group, GroupContent
from gatherer.tools import get_video_lang


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
            print("glitch: no lang code")
            return obj.name('en') #@HACK


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

    # def _video_lang_filter(self):
    #     # @TODO: duplicated code from views.py!!!
    #     # video language
    #     # user changed video lang
    #     request = self.context['request']
    #     if request.method == 'GET':
    #         if request.GET.get('video_lang'):
    #             video_lang = request.GET.get('video_lang')
    #             request.session['video_lang'] = video_lang
    #     # no video lang selected -> show all videos
    #     if 'video_lang' not in request.session.keys():
    #         request.session['video_lang'] = 'all'
    #     # video lang saved 
    #     session_vlang = request.session['video_lang']
    #     if session_vlang and session_vlang != 'all':
    #         language = [request.session['video_lang'],]
    #     else: # all: show videos in all languages
    #         language = [code for code,_ in settings.LANGUAGES]
    #     return language

    def get_name(self, obj):
        try:
            return obj.name(self.context['request'].LANGUAGE_CODE)
        except KeyError:
            print("glitch: no lang code")
            return obj.name('en') #@HACK

    def get_tags(self, obj):
        try:
            lang_code = self.context['request'].LANGUAGE_CODE
        except KeyError:
            lang_code = 'en'

        video_lang = get_video_lang(self.context['request'])
        tags = Tag.objects.filter(group_id=obj.id, video__isnull=False)
        tags = tags.distinct()
        tags = tags.filter(video__language__in=video_lang)
        # tags = tags.filter(video__is_active = True)
        tags = sorted(tags,
                      key = lambda tag: tag.name(lang_code))
        return TranslatedTagSerializer(tags, many=True,
                                       context=self.context).data

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
        # return truncate(obj.title, 85)
        return obj.title

    def get_description(self, obj):
        return obj.description

    def get_publisher(self, obj):
        return truncate(str(obj.publisher), 35)

    def get_published_at(self, obj):
        return _("%s ago") % timesince(obj.published_at,
                                       time_strings=TIME_STRINGS)

    def get_type(self, obj):
        type = obj.type.replace("video", "")
        return type.capitalize()
