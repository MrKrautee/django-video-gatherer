import logging
from django.conf import settings

#from gatherer.lib.youtube import YoutubeFinder
from video_finder.video_finder import YoutubeFinder
from video_finder.video_finder import VideoDuration, VideoEmbeddable, EventType
from gatherer.fb_video_finder import FacebookVideoFinder
_logger = logging.getLogger("django")

youtube_finder = YoutubeFinder(settings.YOUTUBE_API_KEY, logger=_logger)
facebook_finder = FacebookVideoFinder(logger=_logger)

__ALL__ = ["youtube_finder", "VideoDuration", "VideoEmbeddable", "EventType",
           "facebook_finder"]
