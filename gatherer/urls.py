from django.urls import path
from gatherer.views import VideoListView, TagListView, google_login, google_callback

# urlpatterns = [
#         path('ajax/', videos_view, name="videos_by_tag"),
#         path('', VideoList.as_view(), name="videos"),
#         path('<tag>/', VideoList.as_view(), name="videos_by_tag"),
# ]
urlpatterns = [
    path('rest/tags/', TagListView.as_view({'get': 'list'}), name="rest_tags"),
    path('', VideoListView.as_view({'get': 'list'}), name="video_filter"),
]
