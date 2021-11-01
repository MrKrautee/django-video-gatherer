
from django.core.management.base import BaseCommand, CommandError

from gatherer.models import Update
from gatherer.models import Video

class Command(BaseCommand):
    help = 'Group videos by Tags using TagKeyword(s)'


    def handle(self, *args, **options):
        Video.objects.auto_tag(Video.objects.all())
        if True:
            self.stdout.write(self.style.SUCCESS(f"videos taged."))
        else:
            self.stdout.write(self.style.SUCCESS(f"no videos added."))
