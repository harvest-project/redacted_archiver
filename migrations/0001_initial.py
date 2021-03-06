# Generated by Django 2.1.7 on 2019-03-28 00:58

from django.db import migrations, models


def create_initial_archiver_state(apps, schema_editor):
    RedactedArchiverState = apps.get_model('redacted_archiver', 'RedactedArchiverState')
    RedactedArchiverState.objects.create(
        is_enabled=False,
        last_meta_tracker_id=0,
    )


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='RedactedArchiverState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_enabled', models.BooleanField()),
                ('is_download_enabled', models.BooleanField(default=False)),
                ('last_meta_tracker_id', models.BigIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='RedactedSiteLogEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(
                    choices=[('torrent_upload', 'torrent_upload'), ('torrent_edit', 'torrent_edit'),
                             ('torrent_delete', 'torrent_delete'),
                             ('torrent_inactivity_delete', 'torrent_inactivity_delete'),
                             ('request_created', 'request_created'), ('request_filled', 'request_filled'),
                             ('request_unfilled', 'request_unfilled'), ('collage_created', 'collage_created'),
                             ('collage_deleted', 'collage_deleted')], max_length=64, null=True)),
                ('redacted_id', models.BigIntegerField(db_index=True)),
                ('created_datetime', models.DateTimeField()),
                ('text', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='RedactedTorrentToFetch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tracker_id', models.BigIntegerField(unique=True)),
            ],
        ),
        migrations.RunPython(create_initial_archiver_state, migrations.RunPython.noop),
    ]
