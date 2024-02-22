from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import os
import requests
import json
from io import StringIO
import boto3
from dotenv import load_dotenv


load_dotenv()


API_KEY = os.getenv("API_KEY")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")


CURRENT_DATE = datetime.now().date()
FETCH_FROM = CURRENT_DATE - timedelta(days=30)
KEYWORDS = ["Artificial Intelligence", "AI"]




def get_data(resource: str, keyword:str, from_date=FETCH_FROM_DATE):
  base_url = "http://newsapi.org/v2"
    endpoint_url = f"{base_url}/{resource}?apiKey={API_KEY}"
    if resource == "everything":
        endpoint_url = f"{endpoint_url}&q={keyword}&from={from_date}&sortBy=publishedAt"

    return requests.get(endpoint_url).json()




def transform_keyword(keywords: list):
  keyword_list = []
  for word in keywords:
    keyword_list.append(word.lower().replace(" ", "+"))
  return keyword_list





class Extract_data:
  def __init__(self, **context) -> str:
    keyword = KEYWORDS
    querystr = transform_keyword(keyword)
    news_data = pd.DataFrame()
    for query in querystr:
      data = get_data("everything", query)
      news_data = pd.concat([news_data, pd.DataFrame(data["articles"])])

      if len(news_data) == 0 or news_data.empty:
        raise ValueError("API key error")
      
      try:
        news_data["source"] = news_data["source"].apply(lambda x: x["name"])
      except ValueError:
        print("Invalid source")

      news_data.insert(0, "key", query)
      news_data = news_data.append(
          news_data[["source", "title", "description", "key", "content"]] 
      )

    return news_data, querystr






class Transform_data:
  def __init__(self, **context) -> str:
    news_data = context["task_instance"].xcom_pull(task_ids="extract_data")
    csv_buffer = StringIO()
    return csv_buffer, news_data




class Load_data:
  def __init__(self, **context) -> str:
    csv_buffer, news_data = context["task_instance"].xcom_pull(task_ids="transform_data")
    for query in querystr:
      news_data.to_csv(csv_buffer, index=False)
      try:
        s3_resource = boto3.resource(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

        s3_resource.Object(BUCKET_NAME, f"{query}.csv").put(Body=csv_buffer.getvalue())
      except Exception as e:
        print("AWS access not allowed")

    return "Data loaded successfully"



default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 2, 20),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


dag = DAG(
    "news_api_dag",
    default_args=default_args,
    description="News API",
    schedule_interval="@daily",
    catchup=False,
)


extract_data = PythonOperator(
    task_id="extract_data",
    provide_context = True,
    python_callable=Extract_data(),
    dag=dag,
)


transform_data = PythonOperator(
    task_id="transform_data",
    provide_context = True,
    python_callable=Transform_data(),
    dag=dag,
)


load_data = PythonOperator(
    task_id="load_data",
    provide_context = True,
    python_callable=Load_data(),
    dag=dag,
)


extract_data >> transform_data >> load_data



