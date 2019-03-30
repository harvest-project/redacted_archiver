from django.db import transaction, IntegrityError

from Harvest.utils import get_logger
from plugins.redacted.models import RedactedTorrent
from plugins.redacted_archiver.html_parser import parse_site_log
from plugins.redacted_archiver.models import RedactedSiteLogEntry, RedactedTorrentToFetch

logger = get_logger(__name__)


def scrape_log(client):
    first_scan = not RedactedSiteLogEntry.objects.exists()
    completed_scan = False
    tracker_ids = set()

    def add_group(group_id):
        group_tracker_ids = RedactedTorrent.objects.filter(torrent_group_id=group_id).values_list('id', flat=True)
        for group_tracker_id in group_tracker_ids:
            tracker_ids.add(group_tracker_id)

    for page in range(1, 21):
        logger.debug('Requesting log page {}.', page)
        log_entries = parse_site_log(client.get_site_log(page))
        with transaction.atomic():
            for log_entry in log_entries:
                data = log_entry.pop('data', {})
                _, created = RedactedSiteLogEntry.objects.get_or_create(
                    redacted_id=log_entry['redacted_id'],
                    defaults=log_entry,
                )
                if not created:
                    logger.debug('Discovered existing log entry {}.', log_entry['redacted_id'])
                    completed_scan = True
                    break
                if log_entry['action'] == RedactedSiteLogEntry.ACTION_GROUP_RENAME:
                    add_group(data['group_id'])
                if 'torrent_id' in data:
                    tracker_ids.add(data['torrent_id'])
        if completed_scan:
            break

    if not completed_scan and not first_scan:
        logger.error('Not first scan ran out of pages!')

    logger.debug('Discovered {} torrents to fetch.', len(tracker_ids))
    for tracker_id in tracker_ids:
        with transaction.atomic():
            try:
                RedactedTorrentToFetch.objects.create(tracker_id=tracker_id)
            except IntegrityError:
                pass
