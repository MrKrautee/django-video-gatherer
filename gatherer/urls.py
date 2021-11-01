from django.urls import path
from gatherer.views import VideoListView, TagListView
from gatherer.views import GroupListView, TagVideoPreview

urlpatterns = [
    path('rest/group/preview/', TagVideoPreview.as_view({'get': 'list'}),
         name="rest_group_preview"),

    path('rest/tags/', TagListView.as_view({'get': 'list'}), name="rest_tags"),

    path('rest/groups/', GroupListView.as_view({'get': 'list'}),
         name="rest_groups"),

    path('rest/videos/', VideoListView.as_view({'get': 'list'}),
         name="video_filter"),
]
