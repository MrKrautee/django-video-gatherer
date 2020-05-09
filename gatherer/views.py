from django.shortcuts import render
from django.views.generic import ListView
from django.shortcuts import get_object_or_404


from .models import Video
from .models import Tag

class VideoList(ListView):
    model = Video
    filters = { 
            "-published_at": "Datum ab",
            "published_at": "Datum auf",
            "-duration": "Dauer ab",
            "duration": "Dauer auf",
    }
                


    def get_queryset(self):
        order_by = 'published_at'
        if self.request.method == 'GET':
            order_by = self.request.GET.get('order_by', order_by)
        if 'tag' in self.kwargs.keys():
            tag = self.kwargs['tag']
            qs = Video.objects.filter(tags__name=tag)
        else:
            qs = Video.objects.all()
        qs = qs.order_by(order_by)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tags = Tag.objects.filter(video__isnull=False).distinct()
        context['tags'] = tags
        context['filters'] = self.filters
        order_by = 'published_at'
        if self.request.method == 'GET':
            order_by = self.request.GET.get('order_by', order_by)
        context['order_by'] = order_by
        tag = ''
        if 'tag' in self.kwargs.keys():
            tag = self.kwargs['tag']
        context['current_tag'] = tag
        return context
