from airflow import DAG
from airflow.operators.python import PythonOperator
from transformers import pipeline
from airflow.operators.sensors import ExternalTaskSensor
from datetime import datetime, timedelta
import boto3
import os
import json


API_KEY = os.getenv("API_KEY")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")


model = "dheeraj-kj/T5_Model"


def summarize_content_from_s3(**context):
    summarization_pipeline = pipeline("summarization", model = model)

    s3_resource = boto3.resource(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    obj = s3_resource.Object(BUCKET_NAME, "your_data.csv")
    data = obj.get()["Body"].read().decode("utf-8")

    summarized_data = summarization_pipeline(data)

    summarized_data_str = summarized_data[0]['summary_text']
    s3_resource.Object(BUCKET_NAME, "summarized_data.txt").put(Body=summarized_data_str)

    return "Content summarized and stored in S3"



default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 2, 21),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'summarize_content_dag',
    default_args=default_args,
    description='DAG to summarize content from S3',
    schedule_interval=None,
)

summarize_content_task = PythonOperator(
    task_id="summarize_content",
    provide_context=True,
    python_callable=summarize_content_from_s3,
    dag=dag,
)

wait_extract_news = ExternalTaskSensor(
    task_id='wait_extract_news',
    external_dag_id='extract_dag',  
    external_task_id=None,  
    timeout=2000,
    dag=dag,
    mode='reschedule',
    allowed_states=["success"]
)



wait_extract_news >> summarize_content_task
