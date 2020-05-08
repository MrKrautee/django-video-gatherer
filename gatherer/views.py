from django.shortcuts import render
from django.views.generic import ListView
from django.shortcuts import get_object_or_404


from .models import Video
from .models import Tag

class VideoList(ListView):
    model = Video


    def get_queryset(self):
        order_by = 'published_at'
        if 'tag' in self.kwargs.keys():
            tag = self.kwargs['tag']
            qs = Video.objects.filter(tags__name=tag)
        else:
            qs = Video.objects.all()
        qs.order_by(order_by)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tags = Tag.objects.filter(video__isnull=False).distinct()
        context['tags'] = tags
        return context
