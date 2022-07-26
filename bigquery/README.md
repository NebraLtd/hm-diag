# Steps to follow for adding a new diagnostic value to bigquery:

- add a new column to diagnostic or events table in bigquery using console, preferably on a test table. We don't want to do changes in production table before code changes are pushed to fleet.
- export schema from bigquery:
    ```
    eg.
    bq show --schema --format=prettyjson nebra-production:hotspot_diagnostics_data.diagnostics | jq > diag_schema.json
    bq show --schema --format=prettyjson nebra-production:hotspot_events_data.events | jq > events_schema.json
    ```
- to create a new table from schema from gcloud cli in case it doesn't exist yet:
    ```
    bq mk --schema <schema file> <project:<dataset>.<tablename>
    ```
- convert biqguery schema to pydantic model
    ```
    eg.
    python bigquery_to_pydantic.py  --input bq_schema.json --output ../hw_diag/diagnostics/bigquery_data_model.py -- model DiagnosticDataModel
    python3 bigquery_to_pydantic.py --input events.schema --output ../hw_diag/utilities/events_bq_data_model.py --model EventDataModel
    ```

Use the generated model to upload json to respective bucket for ingestion.
