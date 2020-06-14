import logging
from django.conf import settings

#from gatherer.lib.youtube import YoutubeFinder
from video_finder.video_finder import YoutubeFinder
from video_finder.video_finder import VideoDuration, VideoEmbeddable, EventType
_logger = logging.getLogger("django")

youtube_finder = YoutubeFinder(settings.YOUTUBE_API_KEY, logger=_logger)

__ALL__ = ["youtube_finder", "VideoDuration", "VideoEmbeddable", "EventType"]
