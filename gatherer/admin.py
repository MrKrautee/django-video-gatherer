import logging
import urllib

from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path



from gatherer.models import Video
from gatherer.models import Tag
from gatherer.models import YtSearchPattern
from gatherer.models import YtChannel
from gatherer.models import Update
from gatherer.tools import youtube_finder
logger = logging.getLogger("django")

# -----
from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.admin.utils import model_ngettext
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _, gettext_lazy
from django.forms import modelformset_factory

#dev tools
import pprint


def _pprint(dict_like):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(dict_like)

def add_tags(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    app_label = opts.app_label

    #!HACK: use model form to get fancy autocomple in an easy was
    title = _("Are you sure?")
    ModelForm = modeladmin.get_form(request)

    # The user has already confirmed the deletion.
    # Do the deletion and return None to display the change list view again.
    if request.POST.get('post'):
        form = ModelForm(request.POST)
        tag_ids = form.data.getlist('tags')
        tags = Tag.objects.filter(id__in = tag_ids)
        for q in queryset:
            q.tags.add(*tags)
        #!TODO:  add tags to model
        n = queryset.count()
        if n:
            #modeladmin.delete_queryset(request, queryset)
            modeladmin.message_user(request, _("Successfully deleted %(count)d %(items)s.") % {
                "count": n, "items": model_ngettext(modeladmin.opts, n)
            }, messages.SUCCESS)
        # Return None to display the change list page again.
        return None

    objects_name = model_ngettext(queryset)
    admin_form = helpers.AdminForm(
        ModelForm(),
        [(None, {'fields': ['tags', ]})],
        {},
        [],
        model_admin=modeladmin)
    media = modeladmin.media + admin_form.media
    context = {
        **modeladmin.admin_site.each_context(request),
        'admin_form':admin_form,
        'title': title,
        'objects_name': str(objects_name),
        'queryset': queryset,
        'opts': opts,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'media': media,
    }


    request.current_app = modeladmin.admin_site.name

    return TemplateResponse(request, modeladmin.add_tags_template or [
        "admin/%s/%s/action_add_tags.html" % (app_label, opts.model_name),
        "admin/%s/action_add_tags.html" % app_label,
        "admin/action_add_tags.html"
    ], context)
add_tags.short_description = "Add Tags"

class VideoAdmin(admin.ModelAdmin):
    list_display = ('is_active', 'title', 'short_description', 'tags_list',
        'duration', 'published_at', 'update')
    list_display_links = ('title', )
    list_per_page=300
    search_fields = ('title', 'description')
    list_filter = ('is_active', 'tags__name')
    actions = ['activate', 'deactivate', add_tags]
    autocomplete_fields = ['tags']
    readonly_fields = ('title', 'description', 'link', 'image', 'duration',
            'published_at', 'update')

    add_tags_template = ""

    def tags_list(self, obj):
        return [ a for a in obj.tags.all()]
    tags_list.short_description = "Tags"
    tags_list.admin_order_field = 'tags'

    def short_description(self, obj):
        return obj.description[:500]
    short_description.short_description = "Description"

    def activate(self, request, queryset):
        rows_updated = queryset.update(is_active=True)
        if rows_updated == 1:
            message_bit = "1 video was"
        else:
            message_bit = "%s videos were" % rows_updated
        self.message_user(request, "%s successfully marked as active." % message_bit)
    activate.short_description = "Mark as active"

    def deactivate(self, request, queryset):
        rows_updated = queryset.update(is_active=False)
        if rows_updated == 1:
            message_bit = "1 video was"
        else:
            message_bit = "%s videos were" % rows_updated
        self.message_user(request, "%s successfully marked as not active." % message_bit)
    deactivate.short_description = "Mark as not active"

    #def get_urls(self):
    #    urls = super().get_urls()
    #    opts = self.opts
    #    my_urls = [
    #            path('list/', self.admin_site.admin_view(self.gather_videos_view)),
    #            path('list/json/',
    #                self.admin_site.admin_view(self.gather_videos_rest),
    #                name="%s_%s_content"%(opts.app_label, opts.model_name)
    #            ),
    #    ]
    #    return my_urls + urls

    #def gather_videos_rest(self, request, page_token=None):
    #    videos = youtube_finder.search("UCV73LMcuZQfH5If9JBFb43Q","Yogastunde")
    #    context = dict(
    #            videos=videos,
    #            )
    #    return TemplateResponse(request, "admin/video_table.html",context)

    #def gather_videos_view(self, request):
    #    opts = self.opts
    #    context = dict(
    #            **self.admin_site.each_context(request),
    #            title="List Videos",
    #            opts = opts,
    #            app_label = opts.app_label,
    #            media = self.media,
    #            has_view_permission = self.has_view_permission(request),
    #    )
    #    #!TODO: show error
    #    return TemplateResponse(request, "admin/list_videos.html", context)



class YtSearchPatternAdmin(admin.ModelAdmin):
    list_display = ('channel', 'search_query', 'duration', 'event_type')
    autocomplete_fields = ('channel', 'tags' )
    fieldsets = (
        ("Search", {
            'fields': ('channel', 'duration', 'event_type', 'search_query')
        }),
        ("add to Videos", {
            'fields': ('tags',)
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
                    'duration': params['duration'],
                    'event_type': params['event_type'], }
            videos = youtube_finder.search_videos(**search_params)
            context = dict(
                    videos=videos,
                    opts = self.opts,
            )
        else:
            #ERROR: request method not allowed
            pass
        #!TODO: show error
        return TemplateResponse(request, "admin/video_table.html",context)

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
    list_display = ('date_time',)

admin.site.register(Video, VideoAdmin)
admin.site.register(YtSearchPattern, YtSearchPatternAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(YtChannel, YtChannelAdmin)
admin.site.register(Update, UpdateAdmin)
