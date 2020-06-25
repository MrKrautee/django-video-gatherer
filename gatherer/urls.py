from django.urls import path
from gatherer.views import VideoList, videos_view

urlpatterns = [
        path('ajax/', videos_view, name="videos_by_tag"),
        path('', VideoList.as_view(), name="videos"),
        path('<tag>/', VideoList.as_view(), name="videos_by_tag"),
]
