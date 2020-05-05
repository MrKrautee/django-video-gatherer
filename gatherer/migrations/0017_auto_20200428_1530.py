# Generated by Django 3.0.5 on 2020-04-28 15:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gatherer', '0016_ytsearchpattern_yt_channel'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='ytsearchpattern',
            unique_together={('yt_channel', 'search_query')},
        ),
        migrations.RemoveField(
            model_name='ytsearchpattern',
            name='channel_id',
        ),
    ]
