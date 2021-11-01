from django.urls import path
from gatherer.views import VideoListView, TagListView
# , google_login, google_callback
from gatherer.views import GroupListView, TagVideoPreview
# from gatherer.views import video_filter_entry

# urlpatterns = [
#         path('ajax/', videos_view, name="videos_by_tag"),
#         path('', VideoList.as_view(), name="videos"),
#         path('<tag>/', VideoList.as_view(), name="videos_by_tag"),
# ]
urlpatterns = [
    path('rest/group/preview/', TagVideoPreview.as_view({'get': 'list'}),
         name="rest_group_preview"),

    path('rest/tags/', TagListView.as_view({'get': 'list'}), name="rest_tags"),

    path('rest/groups/', GroupListView.as_view({'get': 'list'}),
         name="rest_groups"),

    path('rest/videos/', VideoListView.as_view({'get': 'list'}),
         name="video_filter"),
    # path('', video_filter_entry, name="video_filter"),
]
