import logging
import re
from datetime import datetime

import pytz
from bs4 import BeautifulSoup

from Harvest.utils import get_logger
from plugins.redacted_archiver.models import RedactedSiteLogEntry

logger = get_logger(__name__)

ACTION_REGEX = {
    RedactedSiteLogEntry.ACTION_ARTIST_MERGE: r'^Artist (?P<artist_id>\d+).*was merged into artist.*$',
    RedactedSiteLogEntry.ACTION_ARTIST_DELETE: r'^Artist.*was deleted by.*$',
    RedactedSiteLogEntry.ACTION_GROUP_RENAME: r'^Torrent Group (?P<group_id>\d+).*was renamed to.*from.*$',
    RedactedSiteLogEntry.ACTION_GROUP_ADD_ARTIST: r'^Artist.*was added to the group.*by.*$',
    RedactedSiteLogEntry.ACTION_GROUP_REMOVE_ARTIST: r'^Artist.*was removed from the group.*by.*$',
    RedactedSiteLogEntry.ACTION_GROUP_AUTOMATIC_DELETE: r'^Group.*automatically deleted.*$',
    RedactedSiteLogEntry.ACTION_TORRENT_UPLOAD: r'^Torrent (?P<torrent_id>\d+) .* was uploaded by (?P<user>\S+).*$',
    RedactedSiteLogEntry.ACTION_TORRENT_EDIT: r'^Torrent (?P<torrent_id>\d+) .* was edited by (?P<user>\S+).*$',
    RedactedSiteLogEntry.ACTION_TORRENT_DELETE: r'^Torrent (?P<torrent_id>\d+) .* was deleted by (?P<user>\S+).*$',
    RedactedSiteLogEntry.ACTION_TORRENT_INACTIVITY_DELETE:
        r'^Torrent (?P<torrent_id>\d+) .* was deleted for inactivity.*$',
    RedactedSiteLogEntry.ACTION_REQUEST_CREATED: r'^Request.*was created by user.*$',
    RedactedSiteLogEntry.ACTION_REQUEST_FILLED: r'^Request.*was filled by user.*$',
    RedactedSiteLogEntry.ACTION_REQUEST_UNFILLED: r'^Request.*was unfilled.*$',
    RedactedSiteLogEntry.ACTION_COLLAGE_CREATED: r'^Collage.*was created by.*$',
    RedactedSiteLogEntry.ACTION_COLLAGE_DELETED: r'^Collage.*was deleted by.*$',
}


def _parse_log_entry_row(row):
    col_time, col_content = row.find_all('td')
    time_span = col_time.find('span', class_='time tooltip')

    if not row['id'].startswith('log_'):
        raise Exception('Invalid row id {}.'.format(row['id']))
    log_entry = {
        'action': None,
        'redacted_id': int(row['id'][4:]),
        'created_datetime': datetime.strptime(
            time_span['title'], '%b %d %Y, %H:%M').replace(tzinfo=pytz.utc),
        'text': col_content.text.strip(),
    }

    for action, regex_str in ACTION_REGEX.items():
        match = re.match(regex_str, log_entry['text'])
        if match is not None:
            log_entry['action'] = action
            log_entry['data'] = match.groupdict()

    if log_entry['action'] is None:
        logger.warning('Unable to parse Redacted log row: "{}".', log_entry['text'])

    return log_entry


def parse_site_log(html):
    soup = BeautifulSoup(html, 'html5lib')
    log_table = soup.find('table', class_='log_table')
    log_entries = []
    for row in log_table.find('tbody', recursive=False).find_all('tr', recursive=False):
        if 'colhead' in row.get_attribute_list('class'):
            continue
        log_entries.append(_parse_log_entry_row(row))
    return log_entries
