
from django.core.management.base import BaseCommand

from gatherer.models import Video


class Command(BaseCommand):
    help = 'Group videos by Tags using TagKeyword(s)'

    def handle(self, *args, **options):
        Video.objects.auto_tag(Video.objects.all())
        if True:
            self.stdout.write(self.style.SUCCESS("videos taged."))
        else:
            self.stdout.write(self.style.SUCCESS("no videos added."))
