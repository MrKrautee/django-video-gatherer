# Generated by Django 3.0.5 on 2020-04-27 10:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gatherer', '0010_remove_video_yt_search_patter'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField()),
            ],
        ),
        migrations.AddField(
            model_name='video',
            name='tags',
            field=models.ManyToManyField(null=True, to='gatherer.Tag'),
        ),
    ]
