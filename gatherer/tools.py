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
TOOLS = ["get_video_lang",]
DEV_TOOLS = ['pprint_dict',]
__ALL__ = [ *VIDEO_STUFF, *TOOLS, *DEV_TOOLS]

youtube_finder = YoutubeFinder(settings.YOUTUBE_API_KEY, logger=_logger)
facebook_finder = FacebookVideoFinder(logger=_logger)

#dev tools
def pprint_dict(dict_like:dict):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(dict_like)


def get_video_lang(request):
    """ get users video_lang.

    Returns
    -------
    string
        language code - ie: 'de'
    """
    # video language
    # user changed video lang
    if request.method == 'GET':
        if request.GET.get('video_lang'):
            video_lang = request.GET.get('video_lang')
            request.session['video_lang'] = video_lang
    # no video lang selected -> show all videos
    if 'video_lang' not in request.session.keys():
        request.session['video_lang'] = 'all'
    # video lang saved 
    session_vlang = request.session['video_lang']
    if session_vlang and session_vlang != 'all':
        language = [request.session['video_lang'],]
    else: # all: show videos in all languages
        language = [code for code,_ in settings.LANGUAGES]
    return language
