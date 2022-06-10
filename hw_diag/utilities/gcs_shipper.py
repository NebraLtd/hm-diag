import os
import datetime
import requests
import logging
from hashlib import sha256
from hw_diag.diagnostics.bigquery_data_model import DiagnosticDataModel


log = logging.getLogger()
log.setLevel(logging.DEBUG)


BUCKET_NAME = os.getenv(
    'DIAGNOSTICS_GCS_BUCKET',
    'helium-miner-data'
)

URL = 'https://www.googleapis.com/upload/storage/v1/b/%s/o?uploadType=media' \
    % BUCKET_NAME


def generate_hash(public_key):
    hashable = '%s-%s' % (public_key, datetime.datetime.utcnow().isoformat())
    return sha256(hashable.encode('utf-8')).hexdigest()


def add_timestamp_to_diagnostics(diagnostics):
    diagnostics['last_updated_ts'] = datetime.datetime.utcnow().timestamp()
    return diagnostics


def upload_diagnostics(diagnostics, ship):
    if not ship:
        log.info("Diagnostics shipping not requested, skipping.")
        return

    log.info('Submitting diagnostics to GCS bucket - %s' % BUCKET_NAME)

    # Hash the PK + DateTime to provide a unique, non identifiable name for the
    # file in the bucket.
    file_name = generate_hash(diagnostics.get('PK'))

    upload_url = '%s&name=%s' % (URL, file_name)
    headers = {'Content-Type': 'application/json'}
    diagnostics = add_timestamp_to_diagnostics(diagnostics)

    try:
        # validate and filter diagnostic data as per big query model
        validated_data = DiagnosticDataModel(**diagnostics)
    except Exception as err:
        log.error(f'Failed to enforce biquery data model on diagnostics dict {err}')
        return False

    content = validated_data.json()

    try:
        resp = requests.post(upload_url, headers=headers, data=content)

        if resp.status_code == 200:
            log.info('Diagnostics Submitted to GCS Bucket Successfully')
            return True
        else:
            log.error(
                'Error submitting diagnostics to GCS bucket: %s - %s'
                % (resp.status_code, resp.text)
            )
            return False
    except Exception as err:
        log.error('Error submitting diagnostics to GCS bucket: %s' % str(err))
        return False
