import logging
import urllib
import re

from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
# add tags
from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.admin.utils import model_ngettext
#from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _, gettext_lazy
from django.utils.html import format_html
from django.forms import modelformset_factory

from gatherer.models import Video
from gatherer.models import Tag
from gatherer.models import YtSearchPattern
from gatherer.models import FbSearchPattern
from gatherer.models import YtChannel
from gatherer.models import FbSite
from gatherer.models import Update
from gatherer.tools import youtube_finder, VideoDuration, EventType
from gatherer.tools import facebook_finder
logger = logging.getLogger("django")

# @TODO: only working for simple serach terms.
def highlight_text(text:str, match:str):
    pattern = re.compile(match, re.IGNORECASE)
    result = pattern.search(text)
    if result:
        hi_match = f'<span style="background-color: #FFFF00">{result.group(0)}</span>'
        new_text = pattern.sub(hi_match, text)
        return format_html(new_text)
    else:
        return text

def highlight_search(videos: list, search_query:str):
    for v in videos:
        v['title'] = highlight_text(v.get('title'), search_query)
        v['description'] = highlight_text(v.get('description'), search_query)
    return videos

class VideoTypeListFilter(admin.SimpleListFilter):
    title = _("video type")
    parameter_name = "type"

    def lookups(self, request, model_admin):
        return [('facebookvideo', 'Facebook'),
                ('youtubevideo', 'YouTube')]
    def queryset(self, request, qs):
        if not self.value():
            return qs
        # @TODO: !!dirty!!
        for video in qs:
            if video.type != self.value():
                qs = qs.exclude(id=video.id)
        return qs

class VideoAdmin(admin.ModelAdmin):
    list_display = ('is_active', 'title', 'short_description', 'tags_list',
        'duration', 'published_at', 'update')
    list_display_links = ('title', )
    list_per_page=300
    search_fields = ('title', 'description')
    list_filter = ('is_active', 'tags__name', 'language', VideoTypeListFilter)
    actions = ['activate', 'deactivate', 'add_tags']
    autocomplete_fields = ['tags']
    readonly_fields = ('title', 'description', 'link_link', 'image_link', 'duration',
            'published_at', 'update', 'search_pattern_link', 'publisher')
    exclude = ('link', 'image')

    def tags_list(self, obj):
        return [ a for a in obj.tags.all()]
    tags_list.short_description = "Tags"
    tags_list.admin_order_field = 'tags'

    def short_description(self, obj):
        return obj.description[:500]
    short_description.short_description = "Description"

    def search_pattern_link(self, obj):
        url = obj.search_pattern.get_admin_url()
        return format_html(f"<a href='{url}'>{obj.search_pattern}</a>")
    search_pattern_link.short_description = "search pattern"

    def link_link(self, obj):
        return format_html(f"<a href='{obj.link}' target='blank'>{obj.link}</a>")
    link_link.short_description = _("link")

    def image_link(self, obj):
        return format_html(f"<a href='{obj.image}' target='blank'>{obj.image}</a>")
    image_link.short_description = _("image")

    # --- ACTIONS
    def activate(self, request, queryset):
        rows_updated = queryset.update(is_active=True)
        if rows_updated == 1:
            message_bit = "1 video was"
        else:
            message_bit = "%s videos were" % rows_updated
        self.message_user(request,
                "%s successfully marked as active." % message_bit)
    activate.short_description = "Mark as active"

    def deactivate(self, request, queryset):
        rows_updated = queryset.update(is_active=False)
        if rows_updated == 1:
            message_bit = "1 video was"
        else:
            message_bit = "%s videos were" % rows_updated
        self.message_user(request,
                "%s successfully marked as not active." % message_bit)
    deactivate.short_description = "Mark as not active"

    def add_tags(self, request, queryset):
        opts = self.model._meta
        app_label = opts.app_label
        #!HACK: use model form to get fancy autocomple in an easy way
        title = _("Add Tags to Video")
        ModelForm = self.get_form(request)
        # The user has already confirmed the deletion.
        # Do the deletion and return None to display the change list view again.
        if request.POST.get('post'):
            form = ModelForm(request.POST)
            tag_ids = form.data.getlist('tags')
            tags = Tag.objects.filter(id__in = tag_ids)
            for q in queryset:
                q.tags.add(*tags)
            n = queryset.count()
            if n:
                self.message_user(request,
                    _("Successfully add tags (%(tags)s) to %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(self.opts, n),
                    "tags": ','.join([str(t) for t in tags]) }, messages.SUCCESS)
            # Return None to display the change list page again.
            return None
        objects_name = model_ngettext(queryset)
        #!HACK: only show input for tags.
        admin_form = helpers.AdminForm( ModelForm(),
            [(None, {'fields': ['tags', ]})],
            {}, [], model_admin=self)
        media = self.media + admin_form.media
        context = {
            **self.admin_site.each_context(request),
            'admin_form':admin_form,
            'title': title,
            'objects_name': str(objects_name),
            'queryset': queryset,
            'opts': opts,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            'media': media,
        }
        request.current_app = self.admin_site.name
        return TemplateResponse(request, [
            "admin/%s/%s/action_add_tags.html" % (app_label, opts.model_name),
            "admin/%s/action_add_tags.html" % app_label,
            "admin/action_add_tags.html"
        ], context)
    add_tags.short_description = "Add Tags"

class SearchPatternAdmin(admin.ModelAdmin):

    autocomplete_fields = ('tags', )
    def tag_list(self, obj):
        return [ a for a in obj.tags.all()]
    tag_list.short_description = "Tags"
    tag_list.admin_order_field = 'tags'

class YtSearchPatternAdmin(SearchPatternAdmin):
    list_display = ('channel', 'search_query', 'duration', 'event_type',
    'tag_list',)
    autocomplete_fields = ('channel', 'tags' )
    fieldsets = (
        ("Search", {
            'fields': ('channel', 'duration', 'event_type', 'search_query')
        }),
        ("add to Videos", {
            'fields': ('tags','language')
        }),
        #('Publish Time', {
        #    #'classes': ('collapsed',),
        #    'fields': ('published_before', 'published_after'),
        #}),
    )

    def channel(self, obj):
        return obj.channel.title
    channel.admin_order_field = 'channel__title'


    def get_urls(self):
        urls = super().get_urls()
        opts = self.opts
        my_urls = [
                path('find/',
                    self.admin_site.admin_view(self.find),
                    name="%s_%s_find"%(opts.app_label, opts.model_name)
                ),
        ]
        return my_urls + urls

    def find(self, request):
        if request.method == "GET":
            params = request.GET
            channel_pk = params['channel_pk']
            channel_id = YtChannel.objects.get(id=channel_pk).channel_id
            search_params = {'channel_id':channel_id,
                    'search_query': params['search_query'],
                    'duration': VideoDuration(params['duration']),}
            event_type = params['event_type']
            if event_type:
                search_params.update({'event_type': EventType(event_type)})
            videos = youtube_finder.search_videos(**search_params)
            context = dict(
                    videos=videos,
                    opts = self.opts,
            )
        else:
            #ERROR: request method not allowed
            pass
        #!TODO: show error
        #!TODO: convert video in Django Video type. 
        #       templates should not depend on the video type of the api 
        return TemplateResponse(request, "admin/video_table.html",context)

class FbSearchPatternAdmin(SearchPatternAdmin):
    list_display = ('site', 'search_query', 'tag_list')
    fieldsets = (
        ("Search", {
            'fields': ('site', 'search_query')
        }),
        ("add to Videos", {
            'fields': ('tags','language')
        }),
    )
    autocomplete_fields = ('tags', 'site')

    def get_urls(self):
        urls = super().get_urls()
        opts = self.opts
        my_urls = [
                path('find/',
                    self.admin_site.admin_view(self.find),
                    name="%s_%s_find"%(opts.app_label, opts.model_name)
                ),
        ]
        return my_urls + urls

    def find(self, request):
        if request.method == "GET":
            params = request.GET
            site_pk = params['site_pk']
            slug = FbSite.objects.get(id=site_pk).slug
            search_query = params['search_query']
            videos = facebook_finder.search(slug, search_query)
            videos = highlight_search(videos, search_query)
            context = dict(
                    videos=videos,
                    opts = self.opts,
            )
        else:
            #ERROR: request method not allowed
            pass
        #!TODO: show error
        #!TODO: convert video in Django Video type. 
        #       templates should not depend on the video type of the api 
        return TemplateResponse(request, "admin/video_table.html",context)

class FbSiteAdmin(admin.ModelAdmin):
    list_display = ('slug', )
    list_display_links = ('slug',)
    search_fields = ('slug',)
    # readonly_fields = ('slug',)

class TagAdmin(admin.ModelAdmin):
    list_display = ('name', )
    search_fields = ['name']

class YtChannelAdmin(admin.ModelAdmin):
    list_display = ('title', 'channel_id')
    list_display_links = ('title', )
    search_fields = ('title', 'channel_id')
    readonly_fields = ('title', 'description')

    def save_model(self, request, obj, form, change):
        channel = youtube_finder.get_channel(obj.channel_id)
        obj.title = channel.title
        obj.description = channel.description
        super().save_model(request, obj, form, change)

class UpdateAdmin(admin.ModelAdmin):
    list_display = ('date_time', 'video_count')
    readonly_fields = ('date_time', 'video_count', 'videos')

    def video_count(self, obj):
        count = obj.video_set.count()
        return count
    video_count.short_description = "video count"
    video_count.admin_order_field = "video"

    def videos(self, obj):
        videos = obj.video_set.all()
        videos_str_list = [
                f"<li style='list-style-type:decimal;'>"
                f"{v.published_at}: {v.title}"
                f"[<a href='{v.get_admin_url()}'>view</a>]</li>" for v in videos]
        videos_str = "".join(videos_str_list)
        return format_html(f"<ul>{videos_str}</ul>")
    videos.short_description = "videos updated"
    #videos.allow_tags = True

admin.site.register(Video, VideoAdmin)
admin.site.register(YtSearchPattern, YtSearchPatternAdmin)
admin.site.register(FbSearchPattern, FbSearchPatternAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(YtChannel, YtChannelAdmin)
admin.site.register(FbSite, FbSiteAdmin)
admin.site.register(Update, UpdateAdmin)
