from django.shortcuts import render
from django.views.generic import ListView
from django.shortcuts import get_object_or_404
from django.conf import settings

from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer

from gatherer.serializers import VideoSerializer
from gatherer.models import Video
from gatherer.models import Tag

class VideoList(ListView):
    model = Video
    order_options = {
            "-published_at": "Datum ab",
            "published_at": "Datum auf",
            "-duration": "Dauer ab",
            "duration": "Dauer auf",
    }
    order_by = '-published_at'

    def _video_lang_filter(self):
        # video language
        # user changed video lang
        if self.request.method == 'GET':
            if self.request.GET.get('video_lang'):
                video_lang = self.request.GET.get('video_lang')
                self.request.session['video_lang'] = video_lang
        # no video lang selected -> show all videos
        if 'video_lang' not in self.request.session.keys():
            self.request.session['video_lang'] = 'all'
        # video lang saved 
        session_vlang = self.request.session['video_lang']
        if session_vlang and session_vlang != 'all':
            language = [self.request.session['video_lang'],]
        else: # all: show videos in all languages
            language = [code for code,_ in settings.LANGUAGES]
        return language


    def get_queryset(self):
        order_by = self.order_by
        if self.request.method == 'GET':
            order_by = self.request.GET.get('order_by', order_by)
        if 'tag' in self.kwargs.keys():
            tag = self.kwargs['tag']
            qs = Video.objects.filter(tags__tagcontent__slug=tag)
        else:
            qs = Video.objects.all()
        qs = qs.filter(language__in=self._video_lang_filter())
        qs = qs.order_by(order_by)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tags = Tag.objects.filter(video__isnull=False).distinct()
        tags = tags.filter(video__language__in=self._video_lang_filter())
        order_by = self.request.GET.get('order_by', self.order_by) \
                if self.request.method == 'GET' else self.order_by
        tag = self.kwargs['tag'] if 'tag' in self.kwargs.keys() else ''

        extra_context = {
                **context,
                'tags': tags,
                'current_tag': tag,
                'order_by': order_by,
                'order_options': self.order_options,
                'video_lang': self.request.session.get('video_lang'),
        }
        return extra_context

class VideoListView(ListModelMixin, GenericViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name="gatherer/videos.html"

    def _video_lang_filter(self):
        # video language
        # user changed video lang
        if self.request.method == 'GET':
            if self.request.GET.get('video_lang'):
                video_lang = self.request.GET.get('video_lang')
                self.request.session['video_lang'] = video_lang
        # no video lang selected -> show all videos
        if 'video_lang' not in self.request.session.keys():
            self.request.session['video_lang'] = 'all'
        # video lang saved 
        session_vlang = self.request.session['video_lang']
        if session_vlang and session_vlang != 'all':
            language = [self.request.session['video_lang'],]
        else: # all: show videos in all languages
            language = [code for code,_ in settings.LANGUAGES]
        return language

    def get_queryset(self):
        lang_filter = self._video_lang_filter()
        order_by = "-published_at"
        if self.request.GET.get('order_by'):
            order_by = self.request.GET.get('order_by') 
        if 'tag' in self.kwargs.keys():
            tag = self.kwargs['tag']
            qs = Video.objects.filter(tags__tagcontent__slug=tag,
                    language__in=lang_filter).order_by(order_by)
        else:
            qs = Video.objects.filter(language__in=lang_filter).order_by(order_by)
        return qs

    def list(self, request, **kwargs):
        tag = kwargs['tag'] if 'tag' in kwargs.keys() else 'all'
        if request.accepted_renderer.format == 'html':
            print("html")
            order_options = {
                    "-published_at": "Datum ab",
                    "published_at": "Datum auf",
                    "-duration": "Dauer ab",
                    "duration": "Dauer auf",
            }

            tags = Tag.objects.filter(video__isnull=False).distinct()
            tags = tags.filter(video__language__in=self._video_lang_filter())
            order_by = request.GET.get('order_by', '-published_at')
            page_nr = request.GET.get('page', 1)

            context = {
                    'tags': tags,
                    'current_tag': tag,
                    'order_by': order_by,
                    'page_nr': page_nr,
                    'order_options': order_options,
                    'video_lang': request.session.get('video_lang'),
            }
            return Response(context)


        print("json")
        return super().list(request)


def videos_view(request):

    order_options = {
            "-published_at": "Datum ab",
            "published_at": "Datum auf",
            "-duration": "Dauer ab",
            "duration": "Dauer auf",
    }

    tags = Tag.objects.filter(video__isnull=False).distinct()
    #tags = tags.filter(video__language__in=self._video_lang_filter())
    order_by = request.GET.get('order_by', '-published_at')

    context = {
            'tags': tags,
            'order_by': order_by,
            'order_options': order_options,
            'video_lang': request.session.get('video_lang'),
    }
    return render(request, "gatherer/videos.html", context)
