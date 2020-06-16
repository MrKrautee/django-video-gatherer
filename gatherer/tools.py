import logging
import pprint
from django.conf import settings

#from gatherer.lib.youtube import YoutubeFinder
from video_finder.video_finder import YoutubeFinder
from video_finder.video_finder import VideoDuration, VideoEmbeddable, EventType
from gatherer.fb_video_finder import FacebookVideoFinder
_logger = logging.getLogger("django")


VIDEO_STUFF = ["youtube_finder", "VideoDuration", "VideoEmbeddable", "EventType",
               "facebook_finder"]
TOOLS = []
DEV_TOOLS = ['pprint_dict',]
__ALL__ = [ *VIDEO_STUFF, *TOOLS, *DEV_TOOLS]

youtube_finder = YoutubeFinder(settings.YOUTUBE_API_KEY, logger=_logger)
facebook_finder = FacebookVideoFinder(logger=_logger)

#dev tools
def pprint_dict(dict_like:dict):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(dict_like)
