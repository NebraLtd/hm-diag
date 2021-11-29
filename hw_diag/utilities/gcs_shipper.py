import json
import os
import datetime
import requests
import logging
import subprocess
from hashlib import sha256
from subprocess import CalledProcessError, TimeoutExpired


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


def convert_diagnostics_to_gcs_payload(diagnostics):
    # We converted RPI to serial_number in the code to support RockPI
    # but in BigQuery we can't change the field name easily so we 
    # convert it back
    if 'serial_number' in diagnostics:
        diagnostics['RPI'] = diagnostics['serial_number']
        del diagnostics['serial_number']

    # Fetch the current timestamp in UTC to fill in the 
    # diagnostics field
    diagnostics['last_updated_ts'] = datetime.datetime.utcnow().timestamp()

    # Run a shell command to fetch uptime from unix system and
    # print out the # of days it's been up
    try:
        diagnostics['uptime_days'] = subprocess.run(
                                                    "uptime | awk '{print $3}'",
                                                    stdout=subprocess.PIPE
                                                   )
    except TimeoutExpired as e:
        diagnostics['uptime_days'] = None
        log.exception(e)
    except CalledProcessError as e:
        diagnostics['uptime_days'] = None
        log.exception(e)
    except Exception as e:
        diagnostics['uptime_days'] = None
        log.exception(e)

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
    diagnostics = convert_diagnostics_to_gcs_payload(diagnostics)
    content = json.dumps(diagnostics)

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
