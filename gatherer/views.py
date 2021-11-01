from django.shortcuts import render
from django.db.models import Q

from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.pagination import PageNumberPagination

from gatherer.serializers import VideoSerializer, TranslatedTagSerializer
from gatherer.serializers import TranslatedGroupSerializer
from gatherer.serializers import TagPreviewSerializer
from gatherer.models import Video
from gatherer.models import Tag
from gatherer.models import Group
from gatherer.tools import get_video_lang


class TagVideoPreviewPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'
    # max_page_size = 10


class VideoFilterView(ListModelMixin, GenericViewSet):
    def list(self, request, **kwargs):
        json_response = super().list(request, **kwargs)
        # add tags
        groups = TranslatedGroupSerializer(
            Group.objects.all(), many=True,
            context=self.get_serializer_context()
        ).data
        data = json_response.data

        # add pages count
        videos_per_page = self.pagination_class.page_size
        pages = data["count"] // videos_per_page
        pages += 1 if data["count"] % videos_per_page > 0 else 0

        data_extended = {"pages": pages, "groups": groups}

        # @TODO: HACK!
        if self.queryset == Video.objects:  # !also used by TagVideoPreview
            # add active tags
            videos = self.get_queryset()
            active_tags = dict.fromkeys(
                    (t.name('en'), t.slug('en')) for v in videos
                    for t in v.tags.filter()
            ).keys()
            active_tags = [{"name": name, "slug": slug}
                           for name, slug in active_tags]
            data_extended.update({"active_tags": active_tags})

        data_extended.update(data)
        json_response.data = data_extended
        return json_response


class VideoListView(VideoFilterView):
    queryset = Video.objects
    serializer_class = VideoSerializer
    # renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def get_queryset(self):
        if self.request.GET.get('order_by'):
            order_by = self.request.GET.get('order_by')
        else:
            order_by = "-published_at"
        lang_filter = get_video_lang(self.request)
        video_filter = {
            "is_active": True,
            'language__in': lang_filter,
        }
        # one tag
        if 'tag' in self.kwargs.keys():
            tag = self.kwargs['tag']
            video_filter.update({
                'tags__tagcontent__slug': tag,
            })
        # more than one tag
        elif self.request.GET.get('tags'):
            print("more than one tag")
            tags = self.request.GET.getlist('tags')
            # get videos with one of the given tags
            video_filter.update({
                'tags__tagcontent__slug__in': tags,
            })
            # get only videos with all given tags
            tag_queries = [~Q(tags__tagcontent__slug=tag) for tag in tags]
            tag_query = tag_queries.pop()
            for q in tag_queries:
                tag_query |= q
            full_query = self.queryset.filter(**video_filter)
            if len(tags) > 1:
                full_query = full_query.exclude(tag_query)
            return full_query.order_by(order_by).distinct()

        return self.queryset.filter(**video_filter
                                    ).order_by(order_by).distinct()

    def get_serializer_context(self):
        return {
            'video_lang': get_video_lang(self.request),
            'lang_code': self.request.LANGUAGE_CODE,
            'request': self.request
        }


class GroupListView(ListModelMixin, GenericViewSet):

    queryset = Group.objects
    serializer_class = TranslatedGroupSerializer
    pagination_class = None

    def get_queryset(self):
        video_lang = get_video_lang(self.request)
        group_filter = {
            'tag__video__language__in': video_lang,
            'tag__video__isnull': False,
            'tag__video__is_active': True
        }
        return self.queryset.filter(**group_filter).distinct()

    def get_serializer_context(self):
        return {
            'video_lang': get_video_lang(self.request),
            'lang_code': self.request.LANGUAGE_CODE,
            'request': self.request
        }


class TagVideoPreview(VideoFilterView):
    queryset = Tag.objects
    serializer_class = TagPreviewSerializer
    pagination_class = TagVideoPreviewPagination

    def get_queryset(self):
        video_lang = get_video_lang(self.request)
        group_name = self.request.GET.get('group', '')
        group_filter = {
            'group__groupcontent__name': group_name,
            'video__language__in': video_lang,
            'video__isnull': False,
            'video__is_active': True
        }
        return self.queryset.filter(**group_filter).distinct()

    def get_serializer_context(self):
        return {
            'video_lang': get_video_lang(self.request),
            'lang_code': self.request.LANGUAGE_CODE,
            'request': self.request
        }


def video_filter_entry(request):
    order_options = {
            "-published_at": "Datum ab",
            "published_at": "Datum auf",
            "-duration": "Dauer ab",
            "duration": "Dauer auf",
    }
    order_by = request.GET.get('order_by', '-published_at')
    page_nr = request.GET.get('page', 1)
    context = {
            'order_by': order_by,
            'page_nr': page_nr,
            'order_options': order_options,
            'video_lang': request.session.get('video_lang'),
    }
    return render(request, "gatherer/videos.html", context)


class TagListView(ListModelMixin, GenericViewSet):

    tag_set = Tag.objects.filter(video__isnull=False)
    queryset = tag_set.distinct()
    serializer_class = TranslatedTagSerializer
    pagination_class = None

    def get_queryset(self):
        print("get queryset")
        video_lang = get_video_lang(self.request)
        tags = self.queryset.filter(video__language__in=video_lang)
        print(self.request.LANGUAGE_CODE)
    #    tags = sorted(tags,
    #                  key = lambda tag: tag.name(self.request.LANGUAGE_CODE))
        # tags = tags.filter(tagcontent__language__in=video_lang)
        return tags

    def get_serializer_context(self):
        return {
            'lang_code': self.request.LANGUAGE_CODE,
            'request': self.request
        }
