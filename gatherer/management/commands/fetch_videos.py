
from django.core.management.base import BaseCommand, CommandError

from gatherer.models import Update

class Command(BaseCommand):
    help = 'Fetch videos from server using the VideoSearchPatthern'


    def handle(self, *args, **options):
        Update.objects.make_update()
        #for SearchPattern in VIDEO_SEARCH_PATTERNS:
        #    sp_objects = SearchPattern.objects.all()
        #    videos = []
        #    for sp in sp_objects:
        #        sp.save_videos()

        self.stdout.write(self.style.SUCCESS("nothing happens! :)"))
