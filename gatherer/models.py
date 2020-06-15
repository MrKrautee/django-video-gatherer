import logging
from datetime import datetime
from datetime import timedelta
from urllib.parse import urljoin

from django.db import models
from django.utils import dateparse
from django.db import transaction

#from gatherer.lib.youtube import YoutubeVideoFinder
from gatherer.tools import youtube_finder, EventType, VideoDuration
from gatherer.tools import facebook_finder
# Create your models here.
logger = logging.getLogger("django")

class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="tag name")
    description = models.TextField(blank=True)

    def __str__(self):
        return "%s" % self.name

class YtChannel(models.Model):
    channel_id = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return "%s" % self.title



class Video(models.Model):

    title = models.CharField(max_length=255)
    description = models.TextField()
    # link to video location  
    link = models.CharField(max_length=255, unique=True)
    # thumbnail link
    image = models.CharField(max_length=255)
    duration = models.DurationField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)

    tags = models.ManyToManyField(Tag, blank=True)
    update = models.ForeignKey('Update', on_delete=models.CASCADE, blank=True)
    #yt_search_patter = models.ForeignKey(YtSearchPattern, 
    #        on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.title}\n\t{self.published_at}"

class YoutubeVideo(Video):
    EVENT_TYPE_CHOICES = [
            ('', 'no broadcasts'),
            (EventType.COMPLETED.value, 'completed broadcasts'),
            (EventType.LIVE.value, 'active broadcasts'),
            (EventType.UPCOMING.value, 'upcoming broadcasts')
    ]
    URL_BASE = "http://youtube.de/watch?v="
    youtube_id = models.CharField(max_length=255, unique=True)
    live_broadcast = models.CharField(max_length=9, choices=EVENT_TYPE_CHOICES,
            default='', blank=True)
    # @TODO: foreign key to channel
    channel_id = models.CharField(max_length=255)

    #def __init__(self, *args, **kwargs):
    #    #if videos in DB this error occurs:
    #    #django.db.utils.IntegrityError: UNIQUE constraint failed: gatherer_video.link
    #    super().__init__(*args, **kwargs)
    #    #self.link = self.URL_BASE + self.video_id

    #def save(self, *args, **kwargs):
    #    #self.link = self.URL_BASE + self.video_id
    #    return super().save(*args, **kwargs)


class SearchPattern(models.Model):
    SEARCH_HELP = "use the Boolean NOT (-) and OR (|) operators to exclude " + \
            "videos or to find videos that are associated with one of several search terms."

    # search parameter
    search_query  = models.CharField(max_length=255, blank=True, help_text=SEARCH_HELP)

    # add to matching videos
    tags = models.ManyToManyField(Tag, blank=True)

    def save_videos(self):
        raise Exception("save_videos is not implemented")

    class Meta:
        abstract = True


class YtSearchPattern(SearchPattern):
    """
        addtional adjustments:
            * search_in_title_only bool
            * not_in_title: string that is not contained in title

    """
    DURATION_CHOICES = [
            (VideoDuration.ANY.value, 'any'),
            (VideoDuration.LONG.value, 'longer than 20 mins'),
            (VideoDuration.MEDIUM.value, 'between 4 and 20 mins'),
            (VideoDuration.SHORT.value, 'less than 4 mins')
    ]
    duration = models.CharField(max_length=6, choices=DURATION_CHOICES,
            default='long')
    event_type = models.CharField(max_length=9, choices=YoutubeVideo.EVENT_TYPE_CHOICES,
            default='', blank=True)
    published_before = models.DateTimeField(blank=True, null=True)
    published_after = models.DateTimeField(blank=True, null=True)
    channel = models.ForeignKey(YtChannel, on_delete=models.CASCADE)

    class Meta:
        unique_together = [['channel', 'search_query']]

    def save_videos(self, update):
        logger.debug("save youtube videos")
        """ fetch videos and save to db. """
        # @TODO: - only fetch new videos:
        #           if videos on the fist page (ordered by date)
        #           not new, there are no new videos.
        #        - need to add serach_videos with result in pages,
        #           to youtube_finder.
        search_params = dict(
                channel_id=self.channel.channel_id,
                search_query=self.search_query,
                duration=VideoDuration(self.duration)
        )
        if self.event_type:
            search_params['event_type'] = EventType(self.event_type)
        # @TODO: current not use:
        # published_before=self.published_before,
        # published_after=self.published_after
        videos = youtube_finder.search_videos(content_details=True,
                **search_params)
        with transaction.atomic():
            video_models_status = [
                    YoutubeVideo.objects.update_or_create(youtube_id=v.video_id,
                        defaults = dict(title=v.title,
                        description=v.description,
                        image=v.image_url,
                        link=v.url,
                        published_at=dateparse.parse_datetime(v.published_at),
                        duration=dateparse.parse_duration(v.duration),
                        youtube_id=v.video_id,
                        channel_id=v.channel_id,
                        update=update,
                        live_broadcast=v.live_broadcast))
                    for v in videos]
            # add tags
            if self.tags.all():
                for obj, _ in video_models_status:
                    obj.tags.add(*self.tags.all())
        return video_models_status #( obj, was_added)

class FbSite(models.Model):
    FB_BASE_URL = "https://www.facebook.com"
    slug = models.CharField(max_length=255, blank=False, unique=True)

    # @TODO: - name
    #        - description / mission 

    @property
    def url(self):
        return urljoin(FB_BASE_URL, self.slug)

    def __str__(self):
        return f"{self.slug}"


class FacebookVideo(Video):
    URL_BASE = "https://facebook.com/"
    URL_TEMPLATE = URL_BASE + "%s/videos/%s"

    site = models.ForeignKey(FbSite, on_delete=models.CASCADE)
    video_id = models.CharField(max_length=255, unique=True)


class FbSearchPattern(SearchPattern):
    site = models.ForeignKey(FbSite, on_delete=models.CASCADE)

    def save_videos(self, update):
        logger.debug("save facebook videos")
        videos = facebook_finder.search(self.site.slug, self.search_query)
        with transaction.atomic():
            video_models_status = [
                    FacebookVideo.objects.update_or_create(video_id=v['video_id'],
                        defaults = {
                            'description': v['description'],
                            'title': v['title'],
                            'image': v['image_url'],
                            'link': v['url'],
                            'published_at':
                                datetime.fromtimestamp(v['published_at']),
                            'duration': timedelta(minutes=v['duration']),
                            'site': self.site,
                            'link': FacebookVideo.URL_TEMPLATE % (self.site.slug,
                                                                 v['video_id']),
                            'video_id': v['video_id'],
                            'update': update,
                        }
                    ) for v in videos]
            if self.tags.all():
                for obj, _ in video_models_status:
                    obj.tags.add(*self.tags.all())
        return video_models_status

    class Meta:
        unique_together = [['site', 'search_query']]


class UpdateManager(models.Manager):

    def make_update(self):
        new_update = self.model()
        new_update.save()
        update_status = []
        for SearchPattern in self.model.VIDEO_SEARCH_PATTERNS:
            sp_objects = SearchPattern.objects.all()
            videos = []
            for sp in sp_objects:
                status = sp.save_videos(new_update)
                update_status.extend(status)
        for video, status in update_status:
            if status:
                video.update = new_update
                video.save()
        return new_update

class Update(models.Model):

    VIDEO_SEARCH_PATTERNS = (YtSearchPattern, FbSearchPattern)
    #VIDEO_SEARCH_PATTERNS = (FbSearchPattern,)

    date_time = models.DateTimeField(auto_now=True)

    objects = UpdateManager()

    def __str__(self):
        return f"{self.date_time.ctime()}"
