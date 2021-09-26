import logging
from datetime import datetime
from datetime import timedelta
from urllib.parse import urljoin

from django.db import models
from django.utils import dateparse
from django.db import transaction
from django.urls import reverse
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from gatherer.tools import youtube_finder, EventType, VideoDuration
from gatherer.tools import facebook_finder

logger = logging.getLogger("django")

LANGUAGE_CHOICES = settings.LANGUAGES

DURATION_CHOICES = [
        (VideoDuration.ANY.value, 'any'),
        (VideoDuration.LONG.value, 'longer than 20 mins'),
        (VideoDuration.MEDIUM.value, 'between 4 and 20 mins'),
        (VideoDuration.SHORT.value, 'less than 4 mins')
]


class Group(models.Model):

    def name(self, lang_code):
        try:
            group_content = self.groupcontent_set.get(language=lang_code)
        except:  # TODO: catch specific Exception
            group_content = self.groupcontent_set.get(
                                        language=settings.LANGUAGE_CODE
                        )
        return group_content.name

    def description(self, lang_code):
        return 'not implemented'

    def __str__(self):
        group_content = self.groupcontent_set.filter(
                            language=settings.LANGUAGE_CODE
                      )[0]
        return str(group_content)


class GroupContent(models.Model):
    language = models.CharField(max_length=3,
                                choices=LANGUAGE_CHOICES,
                                blank=False)
    name = models.CharField(max_length=255, unique=True,
                            verbose_name="tag name")
    description = models.TextField(blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self):
        return "%s" % self.name

    class Meta:
        unique_together = ('group', 'language')

class Tag(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True)

    def name(self, lang_code):
        try:
            tag_content = self.tagcontent_set.get(language=lang_code)
        except:  # TODO: catch specific Exception
            tag_content = self.tagcontent_set.get(
                                        language=settings.LANGUAGE_CODE
                        )
        return tag_content.name

    def slug(self, lang_code):
        try:
            tag_content = self.tagcontent_set.get(language=lang_code)
        except:  # TODO: catch specific Exception
            tag_content = self.tagcontent_set.get(
                                        language=settings.LANGUAGE_CODE
                        )
        return tag_content.slug

    def description(self, lang_code):
        return 'not implemented'

    def __str__(self):
        tag_content = self.tagcontent_set.filter(
                            language=settings.LANGUAGE_CODE
                      )[0]
        return str(tag_content)


class TagContent(models.Model):
    language = models.CharField(max_length=3,
                                choices=LANGUAGE_CHOICES,
                                blank=False)
    name = models.CharField(max_length=255, unique=True,
                            verbose_name="tag name")
    description = models.TextField(blank=True)
    slug = models.SlugField()

    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    def __str__(self):
        return "%s" % self.name

    class Meta:
        unique_together = ('tag', 'language')

class TagKeyword(models.Model):
    keyword = models.CharField(max_length=255, blank=False)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    def __str__(self):
        return "%s" % self.keyword


class YtChannel(models.Model):
    channel_id = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return "%s" % self.title

    def get_admin_url(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label,
                       self._meta.model_name), args=[self.id])


import unicodedata
class VideoManager(models.Manager):

    def auto_tag(self, videos=None, tag=None):
        if videos is None:
            # @HACK: only for test and development. remove for poduction!
            videos = self.all()
        if tag is None:
            tags = Tag.objects.all()
        else:
            tags = [tag]
        print(tags)
        for video in videos:
            logger.info(f"checking {video}...")
            for tag in tags:
                keywords = [tc.name.lower() for tc in tag.tagcontent_set.all()]
                more_kws = [k.keyword.lower() for k in tag.tagkeyword_set.all()]
                keywords.extend(more_kws)
                for k in keywords:
                    k_norm = unicodedata.normalize('NFC', k.lower())
                    video_title_norm = unicodedata.normalize('NFC', video.title.lower())
                    if k_norm in video_title_norm:
                        video.tags.add(tag)
                        logger.info(f"\t>>> <{tag}> added")
                        print(f"added tag {tag} to {video}")
                        break
        logger.info(f"... auto tagging completed")

    def active(self):
        return self.filter(is_active=True)

class Video(models.Model):

    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.CharField(max_length=255)
    duration = models.DurationField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)

    tags = models.ManyToManyField(Tag, blank=True)
    update = models.ForeignKey('Update', on_delete=models.CASCADE, blank=True,
                               null=True)
    language = models.CharField(max_length=3,
                                choices=LANGUAGE_CHOICES, blank=False)

    objects = VideoManager()

    def __str__(self):
        return f"{self.title}\n\t{self.published_at}"

    def get_admin_url(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label,
                       self._meta.model_name), args=[self.id])

    @property
    def type(self):
        facebook = "facebookvideo"
        youtube = "youtubevideo"
        try:
            if self.facebookvideo:
                return facebook
        except:
            pass
        try:
            if self.youtubevideo:
                return youtube
        except:
            pass
        return ""

    @property
    def child(self):
        return getattr(self, self.type)

    @property
    def search_pattern(self):
        return self.child.search_pattern

    @property
    def publisher(self):
        return self.child.publisher

    @property
    def link(self):
        return self.child.link

    class Meta:
        ordering = ['-published_at', ]

def test_tagging():
    vlist = Video.objects.filter(id=1034)
    Video.objects.auto_tag(videos=vlist)

@receiver(post_save, sender=TagContent, dispatch_uid="call_me_once_only_12345")
def tagContent_post_save(sender, instance, **kwargs):
    """ auto tagging after adding new Tag """
    # sender: TagContent
    logger.info("starting auto tagging ...")
    Video.objects.auto_tag(tag=instance.tag)


class YoutubeVideo(Video):
    EVENT_TYPE_CHOICES = [
            ('', 'no broadcasts'),
            (EventType.COMPLETED.value, 'completed broadcasts'),
            (EventType.LIVE.value, 'active broadcasts'),
            (EventType.UPCOMING.value, 'upcoming broadcasts')
    ]
    URL_BASE = "http://youtube.de/watch?v="
    video_id = models.CharField(max_length=255, unique=True)
    live_broadcast = models.CharField(max_length=9, choices=EVENT_TYPE_CHOICES,
                                      default='', blank=True)
    channel = models.ForeignKey(YtChannel, on_delete=models.CASCADE)
    search_pattern = models.ForeignKey("YtSearchPattern",
                                       on_delete=models.CASCADE)

    @property
    def publisher(self):
        return self.channel

    @property
    def link(self):
        return f"{self.URL_BASE}{self.video_id}"


class SearchPattern(models.Model):
    SEARCH_HELP = ("use the Boolean NOT (-) and OR (|) operators to exclude "
                   "videos or to find videos that are associated with one of "
                   "several search terms.")

    # search parameter
    search_query = models.CharField(max_length=255, blank=True,
                                    help_text=SEARCH_HELP)
    # add to matching videos
    tags = models.ManyToManyField(Tag, blank=True)
    language = models.CharField(max_length=3, choices=LANGUAGE_CHOICES,
                                blank=False)

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
    duration = models.CharField(max_length=6, choices=DURATION_CHOICES,
                                default='long')
    event_type = models.CharField(max_length=9,
                                  choices=YoutubeVideo.EVENT_TYPE_CHOICES,
                                  default='', blank=True)
    published_before = models.DateTimeField(blank=True, null=True)
    published_after = models.DateTimeField(blank=True, null=True)
    channel = models.ForeignKey(YtChannel, on_delete=models.CASCADE)

    class Meta:
        unique_together = [['channel', 'search_query']]

    def get_admin_url(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label,
                       self._meta.model_name), args=[self.id])

    def save_videos(self):
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
        # @TODO: currently not used:
        #           * published_before=self.published_before,
        #           * published_after=self.published_after
        videos = youtube_finder.search_videos(content_details=True,
                **search_params)
        with transaction.atomic():
            video_models_status = [
                    YoutubeVideo.objects.update_or_create(video_id=v.video_id,
                        defaults = dict(title=v.title,
                        description=v.description,
                        image=v.image_url,
                        published_at=dateparse.parse_datetime(v.published_at),
                        duration=dateparse.parse_duration(v.duration),
                        video_id=v.video_id,
                        channel=self.channel,
                        live_broadcast=v.live_broadcast,
                        search_pattern=self,
                        language=self.language))
                    for v in videos]
            # add tags
            if self.tags.all():
                for obj, _ in video_models_status:
                    obj.tags.add(*self.tags.all())
        return video_models_status

    def __str__(self):
        return f"{self.channel}, q={self.search_query}, {self.duration}"


class FbSite(models.Model):
    FB_BASE_URL = "https://www.facebook.com"
    slug = models.CharField(max_length=255, blank=False, unique=True)

    # @TODO: - name
    #        - description / mission

    @property
    def url(self):
        return urljoin(self.FB_BASE_URL, self.slug)

    def __str__(self):
        return f"{self.slug}"

    def get_admin_url(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label,
                       self._meta.model_name), args=[self.id])


class FacebookVideo(Video):
    URL_BASE = "https://facebook.com/"
    URL_TEMPLATE = f"{URL_BASE}%s/videos/%s"

    video_id = models.CharField(max_length=255, unique=True)
    site = models.ForeignKey(FbSite, on_delete=models.CASCADE)
    search_pattern = models.ForeignKey("FbSearchPattern",
                                       on_delete=models.CASCADE)

    @property
    def publisher(self):
        return self.site

    @property
    def link(self):
        return self.URL_TEMPLATE % (self.site.slug, self.video_id)


class FbSearchPattern(SearchPattern):
    site = models.ForeignKey(FbSite, on_delete=models.CASCADE)
    duration = models.CharField(max_length=6, choices=DURATION_CHOICES,
            default='long')

    video_model = FacebookVideo

    def update_videos(self):
        videos = self.video_model.objects.filter(search_pattern=self)
        recent_video = videos.order_by("-published_at")[0]
        last_published = recent_video.published_at
        pass

    def save_videos(self):
        logger.debug("save facebook videos")
        videos = facebook_finder.search(self.site.slug, self.search_query)
        with transaction.atomic():
            video_models_status = [
                    FacebookVideo.objects.update_or_create(video_id=v['video_id'],
                        defaults = {
                            'description': v['description'],
                            'title': v['title'],
                            'image': v['image_url'],
                            'published_at':
                                datetime.fromtimestamp(v['published_at']),
                            'duration': timedelta(minutes=v['duration']),
                            'site': self.site,
                            'video_id': v['video_id'],
                            'search_pattern': self,
                            'language': self.language,
                        }
                    ) for v in videos]
            if self.tags.all():
                for obj, _ in video_models_status:
                    obj.tags.add(*self.tags.all())
        return video_models_status

    class Meta:
        unique_together = [['site', 'search_query']]

    def __str__(self):
        return f"{self.site}, q={self.search_query}"

    def get_admin_url(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label,
                       self._meta.model_name), args=[self.id])

class UpdateManager(models.Manager):

    def make_update(self):
        new_update = self.model()
        new_update.save()
        update_status = []
        for SearchPattern in self.model.VIDEO_SEARCH_PATTERNS:
            sp_objects = SearchPattern.objects.all()
            videos = []
            for sp in sp_objects:
                status = sp.save_videos()
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
