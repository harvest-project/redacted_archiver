from django.db import models


class RedactedArchiverState(models.Model):
    is_fetch_missing_enabled = models.BooleanField(default=False)
    is_metadata_enabled = models.BooleanField(default=False)
    is_log_follow_enabled = models.BooleanField(default=False)
    is_download_enabled = models.BooleanField(default=False)
    last_meta_tracker_id = models.BigIntegerField(default=0)


class RedactedSiteLogEntry(models.Model):
    ACTION_ARTIST_MERGE = 'artist_merge'
    ACTION_ARTIST_DELETE = 'artist_delete'
    ACTION_GROUP_RENAME = 'group_rename'
    ACTION_GROUP_ADD_ARTIST = 'group_add_artist'
    ACTION_GROUP_REMOVE_ARTIST = 'group_remove_artist'
    ACTION_GROUP_AUTOMATIC_DELETE = 'group_automatic_delete'
    ACTION_TORRENT_UPLOAD = 'torrent_upload'
    ACTION_TORRENT_EDIT = 'torrent_edit'
    ACTION_TORRENT_DELETE = 'torrent_delete'
    ACTION_TORRENT_INACTIVITY_DELETE = 'torrent_inactivity_delete'
    ACTION_REQUEST_CREATED = 'request_created'
    ACTION_REQUEST_FILLED = 'request_filled'
    ACTION_REQUEST_UNFILLED = 'request_unfilled'
    ACTION_COLLAGE_CREATED = 'collage_created'
    ACTION_COLLAGE_DELETED = 'collage_deleted'

    ACTION_CHOICES = (
        (ACTION_ARTIST_MERGE, ACTION_ARTIST_MERGE),
        (ACTION_ARTIST_DELETE, ACTION_ARTIST_DELETE),
        (ACTION_GROUP_RENAME, ACTION_GROUP_RENAME),
        (ACTION_GROUP_ADD_ARTIST, ACTION_GROUP_ADD_ARTIST),
        (ACTION_GROUP_REMOVE_ARTIST, ACTION_GROUP_REMOVE_ARTIST),
        (ACTION_GROUP_AUTOMATIC_DELETE, ACTION_GROUP_AUTOMATIC_DELETE),
        (ACTION_TORRENT_UPLOAD, ACTION_TORRENT_UPLOAD),
        (ACTION_TORRENT_EDIT, ACTION_TORRENT_EDIT),
        (ACTION_TORRENT_DELETE, ACTION_TORRENT_DELETE),
        (ACTION_TORRENT_INACTIVITY_DELETE, ACTION_TORRENT_INACTIVITY_DELETE),
        (ACTION_REQUEST_CREATED, ACTION_REQUEST_CREATED),
        (ACTION_REQUEST_FILLED, ACTION_REQUEST_FILLED),
        (ACTION_REQUEST_UNFILLED, ACTION_REQUEST_UNFILLED),
        (ACTION_COLLAGE_CREATED, ACTION_COLLAGE_CREATED),
        (ACTION_COLLAGE_DELETED, ACTION_COLLAGE_DELETED),
    )

    action = models.CharField(max_length=64, choices=ACTION_CHOICES, null=True)
    redacted_id = models.BigIntegerField(db_index=True)
    created_datetime = models.DateTimeField()
    text = models.TextField()


class RedactedTorrentToFetch(models.Model):
    tracker_id = models.BigIntegerField(unique=True)
