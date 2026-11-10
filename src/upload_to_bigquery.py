
from pathlib import Path
from google.cloud import bigquery

# Project configuration
PROJECT_ID = "careflow-process-mining-512416"
DATASET_ID = "careflow_dataset"
TABLE_ID = "hospital_event_logs_full"


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_FILE = PROJECT_ROOT / "data" / "raw" / "hospital_event_logs.csv"


client = bigquery.Client(project=PROJECT_ID)


table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"


schema = [
    bigquery.SchemaField("Patient_ID", "STRING"),
    bigquery.SchemaField("Event_ID", "STRING"),
    bigquery.SchemaField("Activity", "STRING"),
    bigquery.SchemaField("Event_Timestamp", "TIMESTAMP"),
    bigquery.SchemaField("Department", "STRING"),
    bigquery.SchemaField("Resource", "STRING"),
]


job_config = bigquery.LoadJobConfig(
    schema=schema,
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
)


if not CSV_FILE.exists():
    raise FileNotFoundError(f"CSV file not found: {CSV_FILE}")

print("Uploading CareFlow event logs to BigQuery...")

with open(CSV_FILE, "rb") as csv_file:
    load_job = client.load_table_from_file(
        csv_file,
        table_ref,
        job_config=job_config

    )

load_job.result()

table = client.get_table(table_ref)


print("\nUpload successful!")
print(f"Table: {table_ref}")
print(f"Total rows uploaded: {table.num_rows}")

print(f"Total columns: {len(table.schema)}")
