from django.db.models import F

from plugins.redacted.client import RedactedClient
from plugins.redacted.models import RedactedTorrent, RedactedArtist
from plugins.redacted.tracker import RedactedTrackerPlugin
from torrents.add_torrent import fetch_torrent
from torrents.models import Realm
from trackers.registry import TrackerRegistry


class MetadataRefresher:
    def __init__(self):
        self.client = RedactedClient()
        self.tracker = TrackerRegistry.get_plugin(
            RedactedTrackerPlugin.name, 'redacted_refresh_metadata')
        self.realm = Realm.objects.get(name=self.tracker.name)

    def refresh_metadata_item(self):
        redacted_torrent = RedactedTorrent.objects.order_by('fetched_datetime').first()
        redacted_artist = RedactedArtist.objects.order_by(
            F('fetched_datetime').asc(nulls_first=True)).first()

        if redacted_torrent is None and redacted_artist is None:
            return None

        should_refresh_artist = redacted_artist is not None and (
                redacted_torrent is None or
                redacted_artist.fetched_datetime is None or
                redacted_artist.fetched_datetime < redacted_torrent.fetched_datetime
        )
        if should_refresh_artist:
            self.tracker.update_artist(self.client, redacted_artist.id)
            return redacted_artist.fetched_datetime
        else:
            fetch_torrent(self.realm, self.tracker, redacted_torrent.id, force_fetch=True)
            return redacted_torrent.fetched_datetime
