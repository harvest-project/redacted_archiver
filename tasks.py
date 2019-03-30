import time

from django.conf import settings
from django.db.models import Q
from huey.contrib.djhuey import db_periodic_task, lock_task

from Harvest.huey_scheduler import Crontab, IntervalSeconds
from Harvest.utils import get_logger
from monitoring.decorators import update_component_status
from monitoring.models import ComponentStatus, LogEntry
from plugins.redacted.client import RedactedClient
from plugins.redacted.exceptions import RedactedTorrentNotFoundException
from plugins.redacted.tracker import RedactedTrackerPlugin
from plugins.redacted_archiver import log_scraper
from plugins.redacted_archiver.models import RedactedArchiverState
from torrents.add_torrent import fetch_torrent
from torrents.models import Realm, Torrent
from trackers.registry import TrackerRegistry

logger = get_logger(__name__)


@db_periodic_task(IntervalSeconds(settings.REDACTED_ARCHIVER_LOG_FOLLOW_INTERVAL))
@lock_task('redacted_archiver_log_follow')
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


@db_periodic_task(IntervalSeconds(settings.REDACTED_ARCHIVER_FETCH_MISSING_INTERVAL))
@lock_task('redacted_archiver_fetch_missing')
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
    tracker = TrackerRegistry.get_plugin(RedactedTrackerPlugin.name, 'redacted_archiver_fetch_missing')
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
            LogEntry.warning('Unable to fetch missing metadata for Redacted torrent {} with info hash {} '
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


@db_periodic_task(Crontab())
@lock_task('redacted_archive_download_torrent')
def redacted_archive_download_torrent():
    state = RedactedArchiverState.objects.get()
    if not state.is_download_enabled:
        return
