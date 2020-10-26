import time

from django.conf import settings
from django.db.models import Q

from Harvest.utils import get_logger
from monitoring.decorators import update_component_status
from monitoring.models import ComponentStatus, LogEntry
from plugins.redacted.client import RedactedClient
from plugins.redacted.exceptions import RedactedTorrentNotFoundException
from plugins.redacted.tracker import RedactedTrackerPlugin
from plugins.redacted_archiver import log_scraper
from plugins.redacted_archiver.metadata_refresh import MetadataRefresher
from plugins.redacted_archiver.models import RedactedArchiverState
from task_queue.task_queue import TaskQueue
from torrents.add_torrent import fetch_torrent
from torrents.models import Realm, Torrent
from trackers.registry import TrackerRegistry

logger = get_logger(__name__)


@TaskQueue.periodic_task(settings.REDACTED_ARCHIVER_LOG_FOLLOW_INTERVAL)
@update_component_status(
    'redacted_archiver_log_follow',
    error_message='Redacted archiver log follow crashed.',
)
def redacted_archiver_log_follow():
    state = RedactedArchiverState.objects.get()
    if not state.is_log_follow_enabled:
        return

    client = RedactedClient()
    log_scraper.scrape_log(client)


@TaskQueue.periodic_task(settings.REDACTED_ARCHIVER_FETCH_MISSING_INTERVAL)
@update_component_status(
    'redacted_archiver_fetch_missing',
    error_message='Redacted archiver fetch missing crashed.',
)
def redacted_archiver_fetch_missing():
    start = time.time()

    state = RedactedArchiverState.objects.get()
    if not state.is_fetch_missing_enabled:
        return

    client = RedactedClient()
    tracker = TrackerRegistry.get_plugin(RedactedTrackerPlugin.name,
                                         'redacted_archiver_fetch_missing')
    realm = Realm.objects.get(name=tracker.name)

    num_fetched = 0
    not_found = set()
    while True:
        torrent_missing_info = Torrent.objects.filter(
            ~Q(info_hash__in=not_found),
            realm=realm,
            torrent_info=None,
        ).first()
        if torrent_missing_info is None:
            break

        try:
            red_data = client.get_torrent_by_info_hash(torrent_missing_info.info_hash)
        except RedactedTorrentNotFoundException:
            not_found.add(torrent_missing_info.info_hash)
            LogEntry.warning(
                'Unable to fetch missing metadata for Redacted torrent {} with info hash {} '
                'downloaded in {} in managed {}. Please check and/or remove from client.'.format(
                    torrent_missing_info.name,
                    torrent_missing_info.info_hash,
                    torrent_missing_info.download_path,
                    torrent_missing_info.client,
                ))
            continue
        tracker_id = str(red_data['torrent']['id'])
        fetch_torrent(realm, tracker, str(tracker_id))
        num_fetched += 1

        allowed_time = (
                settings.REDACTED_ARCHIVER_FETCH_MISSING_INTERVAL -
                settings.REDACTED_ARCHIVER_FETCH_MISSING_SLEEP -
                3
        )
        if time.time() - start >= allowed_time:
            break
        time.sleep(settings.REDACTED_ARCHIVER_FETCH_MISSING_SLEEP)

    remaining_missing = Torrent.objects.filter(realm=realm, torrent_info=None).count()
    time_taken = time.time() - start
    ComponentStatus.update_status(
        'redacted_archiver_fetch_missing',
        ComponentStatus.STATUS_GREEN,
        'Completed Redacted fetch missing run. Fetched {} torrents in {:.3f} s. Not found: {}. Remaining: {}.'.format(
            num_fetched, time_taken, len(not_found), remaining_missing),
    )


@TaskQueue.periodic_task(settings.REDACTED_ARCHIVER_REFRESH_METADATA_INTERVAL)
@update_component_status(
    'redacted_archiver_refresh_metadata',
    error_message='Redacted archiver fetch missing crashed.',
)
def redacted_archiver_refresh_metadata():
    throttler = RedactedClient.get_throttler()
    if throttler.get_load() != 0:
        ComponentStatus.update_status(
            'redacted_archiver_refresh_metadata',
            ComponentStatus.STATUS_YELLOW,
            'Not refreshing Redacted metadata due to client load.',
        )
        return

    refresher = MetadataRefresher()
    start = time.time()
    last_datetime = None
    num_refreshed = 0

    for _ in range(settings.REDACTED_ARCHIVER_REFRESH_METADATA_COUNT):
        last_datetime = refresher.refresh_metadata_item()
        num_refreshed += 1

    ComponentStatus.update_status(
        'redacted_archiver_refresh_metadata',
        ComponentStatus.STATUS_GREEN,
        'Updated {} Redacted items in {:.3f}s, previously last fetched at {}'.format(
            num_refreshed,
            time.time() - start,
            last_datetime,
        ),
    )
