
from django.core.management.base import BaseCommand, CommandError

from gatherer.models import Update
from gatherer.models import Video

class Command(BaseCommand):
    help = 'Fetch videos from server using the VideoSearchPatthern'


    def handle(self, *args, **options):
        update_model = Update.objects.make_update()
        videos_updated = update_model.video_set.all()
        Video.objects.auto_tag(videos_updated)
        self.stdout.write(f"Update videos: {update_model}")
        if len(videos_updated):
            for video in videos_updated:
                self.stdout.write(f"added video: {video}")
            self.stdout.write(self.style.SUCCESS(f"{len(videos_updated)} videos added."))
        else:
            self.stdout.write(self.style.SUCCESS(f"no videos added."))
