# Google Cloud Storage Diagnostics Shipping

HM-Diag provides the capability to periodically ship hotspot diagnostic
statistics to Google Cloud Storage for centralised fleet management / 
feedback for services such as the Nebra Dashboard. Once ingested to Google
Cloud Storage then DataFlow can be used to marshall the statistics into
BigQuery for easy consumption with an SQL-like query language.

### Configure Google Cloud Storage Buckets
- Login to your Google Cloud Project and navigate to Google Cloud Storage.
  + or just head here https://console.cloud.google.com/storage/browser
- Create a new bucket with a sensible, descriptive name e.g.
  "hotspot-diagnostics-ingestion" for storing inbound hotspot diagnostics
  data with the following properties:
  + Location Type: Probably fine to be a single region for development purposes.
    Multi-region should by considered for production deployments.
  + Storage Class: Standard
  + Access Control: Uniform
  + Protection Tools: None
- Once the bucket has been created open the bucket and head to the lifecycle tab.
  Add a new rule to delete objects with an age based condition of 3 days. This will
  auto-delete ingested data from the bucket every 3 days, by this time DataFlow
  should have marshalled the data into BigQuery and it's no longer required within
  the GCS bucket.
- Switch to the permissions tab. Currently diagnostics ingestion is performed without
  credentials and hence the bucket must be publically accessible and allUsers principal
  given the Storage Legacy Bucket Writer role to allow writing to the bucket from the
  hotspot. The allUsers principal should have no other permissions, e.g. read, else
  anonymous users could read diagnostics data for all hotspots.
- Create another bucket for storing DataFlow ingestion scratch space, e.g.
  "hotspot-ingestion-scratch". This bucket does not require any specific
  ACL / roles. Google Cloud will deal with this for you later when you configure
  DataFlow.
- Upload the contents of the bigquery folder of this repository (bq_funcs.js &
  bq_schema.json) into the DataFlow scratch space bucket. This will be used later
  by the DataFlow service.
  
### Define GCS Bucket in Balena Fleet
- Open the fleet of hotspots you'd like to submit diagnostics for and add the following
  variable to enable diagnostics shipping.
  + DIAGNOSTICS_GCS_BUCKET: helium-miner-data

### Configure BigQuery Data Set
- Use the left-hand drawer to navigate to the BigQuery service.
  + or head here https://console.cloud.google.com/bigquery
- In the BigQuery explorer click the actions menu next to your project's name and
  select "Add Data Set". Configure your BigQuery data set as follows:
  + Data Set ID: Something sensible, e.g. "hotspot_diagnostics_data"
  + Data Location: The preferred region for the data set.
  + Encryption: Google Managed Key

### Configure DataFlow Streaming Job
- Use the left-hand drawer to navigate to the DataFlow service.
- Click "Create Job From Template" and configure the job as follows:
  + Name: hotspot_diagnostics_ingestion_stream
  + Region: Should be the same region as your BigQuery data set from the previous step
  + Template: Text Files on Cloud Storage to BigQuery
- Configure the job parameters as follows:
  + JavaScript UDF path in Cloud Storage: gs://helium-miner-data-scratch/bq_funcs.js
  + JSON Path: gs://helium-miner-data-scratch/bq_schema.json
  + JavaScript UDF Name: transform
  + BigQuery Output Table: Your BigQuery table name in the following format;
    * <your_project_id>:<your_dataset_name>.diagnostics
  + Cloud Storage Input Path: gs://helium-miner-data/*
  + Temporary BigQuery Directory: gs://helium-miner-data-scratch/bq_temp
  + Temporary Location: gs://helium-miner-data-scratch/dataflow_temp
  + Encryption: Google Managed Key
- Click "Show Optional Parameters" and update the following:
  + Max Workers: 1 for dev, for production workloads select suitable number for scale of deployment.
  + Machine Type: e2-medium
    * Selected for cost efficiency, although largers nodes may be beneficial for large deployments.
- Click Run Job to start the DataFlow ingestion stream.

### Check Functionality
- Switch to the Cloud Storage service and inspect your inbound data bucket, you should see
  JSON files being written by hotspots with a 64 character hash as the file names.
- Switch to the DataFlow service and check the streaming job is running and has no errors.
- Switch to the BigQuery service, select the diagnostics table and switch to the preview tab, you
  should see data from hotspots displayed in the table.
