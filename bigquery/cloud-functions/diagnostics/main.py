import json
import logging
from google.cloud import storage
from google.cloud import bigquery
import google.cloud.logging

logging_client = google.cloud.logging.Client()
logging_client.setup_logging()
logging.getLogger().setLevel(logging.INFO)


BUCKET_NAME = ''
PROJECT_ID = ''
DATASET_NAME = ''
TABLE_NAME = ''
TABLE_ID = '%s.%s.%s' % (PROJECT_ID, DATASET_NAME, TABLE_NAME)


def insert_into_bigquery(data):
    # If wifi card is failed we cannot insert Bool into String field,
    # so simply replace with blank string.
    if not data.get('W0'):
        data['W0'] = ''

    if 'RPI' in data:
        data['serial_number'] = data['RPI']
        del data['RPI']

    client = bigquery.Client()
    errors = client.insert_rows_json(
        TABLE_ID,
        [data]
    )
    if errors:
        logging.error("Error inserting data to BigQuery - %s" % errors)


def download_file(file_name):
    client = storage.Client()
    bucket = client.get_bucket(BUCKET_NAME)
    blob = bucket.get_blob(file_name)
    data = blob.download_as_string()
    data_dict = json.loads(data.decode('utf-8'))
    return data_dict


def delete_file(file_name):
    client = storage.Client()
    bucket = client.get_bucket(BUCKET_NAME)
    bucket.delete_blob(file_name)


def import_diagnostics_data(event, context):  # NOSONAR
    file_name = event.get('name')
    logging.info(f"Processing file: {file_name}.")
    try:
        data = download_file(file_name)
        logging.info(f"Inserting file {file_name} into BigQuery.")
        insert_into_bigquery(data)
        logging.info(f"Deleting file: {file_name}.")
        delete_file(file_name)
    except Exception as err:
        logging.error(f"Error importing file: {file_name} - {err}")
    logging.info(f"Finished importing file: {file_name}.")
