import logging
import subprocess
import os
import json
import re
from datetime import datetime, timedelta
from facebook_scraper.fb_scraper import FacebookScraper


class FacebookVideoFinder:

    _scraper = FacebookScraper(request_delay=0.5)
    _cache = None
    CACHE_DIR = "."
    CACHE_FILE_NAME = ".fb_video_cache.json"

    def __init__(self, caching=True,
                 caching_delay=timedelta(days=100.0),
                 cache_dir=None,
                 logger=logging.getLogger(__name__)):
        self._logger = logger
        if caching:
            if not cache_dir:
                cache_dir = self.CACHE_DIR
            try:
                os.mkdir(cache_dir)
            except FileExistsError:
                pass
            self._expires = caching_delay
            self._cache_file = "%s/%s" % (os.path.abspath(cache_dir),
                                          self.CACHE_FILE_NAME)
            # Load cache from file
            cache = {}
            if os.path.isfile(self._cache_file):
                with open(self._cache_file, 'r') as f:
                    cached_requests = json.load(f)
                    for fb_site_slug, (time_str, response) \
                            in cached_requests.items():
                        time = datetime.fromtimestamp(time_str)
                        if datetime.now() - time < self._expires:
                            cache[fb_site_slug] = (time_str, response)
            self._cache = cache
            self.get_videos = self._cached_get_videos

    def _get_duration(self, video_src_url):
        result = subprocess.check_output(
                        f'ffprobe -v quiet -show_streams '+
                        f'-select_streams v:0 -of json "{video_src_url}"',
                        shell=True).decode()
        fields = json.loads(result)['streams'][0]
        duration = fields['duration']
        return float(duration)/60

    def _get_videos(self, site_name_slug):
        videos = []
        for video in self._scraper.extract_videos(site_name_slug):
            video['duration'] = self._get_duration(video['src'])
            videos.append(video)
        return videos


    def get_videos(self, site_name_slug):
        return self._get_videos(site_name_slug)

    def _cached_get_videos(self, site_name_slug):
        videos = []
        try:
            time_stamp, response_json = self._cache[site_name_slug]
            time = datetime.fromtimestamp(time_stamp)
            if datetime.now() - time < self._expires:
                self._logger.debug("load videos from cache")
                videos = response_json
                return videos
        except KeyError:
            pass
        self._logger.debug(f"cache videos from {site_name_slug}")
        videos = self._get_videos(site_name_slug)
        if videos:
            self._cache[site_name_slug] = (datetime.now().timestamp(), videos)
            with open(self._cache_file, 'w') as f:
                json.dump(self._cache, f)
        return videos

    def _convert(self, video) -> dict:
        return {
            'video_id': video['id'],
            'image_url': video['thumbnail'],
            'url': video['url'],
            'title': video['text'][:110],
            'description': video['text'],
            'published_at': video['publish_time'],
            'duration': video['duration']

        }
    def search(self, site_name_slug, search_query: str):
        videos = self.get_videos(site_name_slug)
        result_videos = [self._convert(v) for v in videos
                         if re.search(search_query, v['text'], re.IGNORECASE)]
        return result_videos

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    finder = FacebookVideoFinder()
    videos = finder.get_videos("3HOFoundation")
    #videos = finder.search("Kundalini.Yoga.Zentrum", "kriya")
    print(videos)
