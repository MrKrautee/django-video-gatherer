from django.shortcuts import render
from django.views.generic import ListView
from django.shortcuts import get_object_or_404


from .models import Video
from .models import Tag

class VideoList(ListView):
    model = Video
    order_options = {
            "-published_at": "Datum ab",
            "published_at": "Datum auf",
            "-duration": "Dauer ab",
            "duration": "Dauer auf",
    }
    order_by = '-published_at'

    def get_queryset(self):
        order_by = self.order_by
        if self.request.method == 'GET':
            order_by = self.request.GET.get('order_by', order_by)
        if 'tag' in self.kwargs.keys():
            tag = self.kwargs['tag']
            qs = Video.objects.filter(tags__name=tag)
        else:
            qs = Video.objects.all()
        qs = qs.filter(language=self.request.LANGUAGE_CODE)
        qs = qs.order_by(order_by)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tags = Tag.objects.filter(video__isnull=False).distinct()
        order_by = self.request.GET.get('order_by', self.order_by) \
                if self.request.method == 'GET' else self.order_by
        tag = self.kwargs['tag'] if 'tag' in self.kwargs.keys() else ''
        extra_context = {
                **context,
                'tags': tags,
                'current_tag': tag,
                'order_by': order_by,
                'order_options': self.order_options,
        }
        return extra_context
