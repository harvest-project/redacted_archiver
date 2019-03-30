from Harvest.settings import base

REDACTED_ARCHIVER_LOG_FOLLOW_INTERVAL = base.env.int('DJANGO_REDACTED_ARCHIVER_LOG_FOLLOW_INTERVAL', 60)

REDACTED_ARCHIVER_FETCH_MISSING_SLEEP = base.env.float('DJANGO_REDACTED_ARCHIVER_FETCH_MISSING_SLEEP', 5)
REDACTED_ARCHIVER_FETCH_MISSING_INTERVAL = base.env.int('DJANGO_REDACTED_ARCHIVER_FETCH_MISSING_INTERVAL', 120)

REDACTED_ARCHIVER_METADATA_INTERVAL = base.env.int('DJANGO_REDACTED_ARCHIVER_METADATA_INTERVAL', 60)

REDACTED_ARCHIVER_DOWNLOAD_INTERVAL = base.env.int('DJANGO_REDACTED_ARCHIVER_DOWNLOAD_INTERVAL', 60)