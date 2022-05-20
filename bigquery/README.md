# Steps to follow for adding a new diagnostic value to bigquery:

- add a new column to diagnostic table in bigquery using console, preferably on a test table. We don't want to do changes in production table before code changes are pushed to fleet.
- export the desired schema from bigquery:
    ```
    bq show --schema --format=prettyjson nebra-production:hotspot_diagnostics_data.diagnostics | jq > bq_schema.json
    ```
- convert biqguery schema to pydantic model
    ```
    python bigquery_to_pydantic.py  --input bq_schema.json --output ../hw_diag/diagnostics/bigquery_data_model.py
    ```

The generated model is used by hw_diag/utilities/gcs_shipper.py to upload data to bigquery.
