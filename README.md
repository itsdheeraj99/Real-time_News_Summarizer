# Real-time News Summarizer using LLM and Airflow.
## Overview
This project aims to summarize news articles automatically utilizing Python, Airflow, NewsAPI and AWS services like S3 and MWAA. It retrieves news data from the website and transforms it into tabular form to further summarize it using summarising model and store it as a document.

## Implementation
1. **Data Retrieval:** The News articles are extracted from web using [NewsAPI](https://newsapi.org/). It extracts the news articles based on the given keywords. More on the working of this API can be found through its [documentation.](https://newsapi.org/docs)
2. **Summarization:** The retrieved news articles are passed through a Large Language Model (LLM), which generates concise summaries based on the content of those articles. About the training and working of the LLM used here can be found in my this [repository](https://github.com/itsdheeraj99/Text_summarizer_using_LLM).
3. **Document File Creation:** The generated summaries are stored as document files, typically in a format like `.txt` or `.docx`.
4. **Scheduling with Airflow:** The entire process, including data retrieval, summarization, and document file creation, is orchestrated and scheduled using Apache Airflow. Airflow allows for the creation of DAGs, where each node represents a task, and the dependencies between tasks are defined.

## DAGs and Workflow
### Extract DAG
This DAG contains the tasks for data extraction from News API, transforming it into tabular form and storing it in S3 bucket. 
- **Task 1:** Utilizing a Python operator, data is retrieved through the API. This includes Python libraries like `requests` for initiating GET request to API and obtain the required data.
- **Task 2:** After extracting the data, it is strutured into a tabular format with columns of its Author, Title, Content and many such. 
- **Task 3:** Finally, the structured  data is loaded to a S3 bucket. This operation is executed using Python operator and an AWS access key to access the S3 bucket.

### Summarize DAG
This DAG contains the tasks for summarizing the content of the retrieved articles and storing the documents containing the summary of all the collected articles.
- **Task 1:** Utilizing an `ExternalTaskSensor` operator which triggers the next DAG or task in the data pipeline when an external task is completed. This task waits until the extract_dag is not completed. Once on the previous DAG is successful this task triggers and initiates the summarize dag.
- **Task 2:** This DAG collects the content of the articles and passes through the summarizing LLM, which is called through Hugging Face transformer's pipeline API to make a GET request to the model saved on the Hugging Face hub. On passing the text of content through the model, it returns a summarized text which is loaded into a S3 bucket in `.docx` or `.txt` file format. 

## Conclusion
By following these tasks an end to end workflow is established in AWS WMAA. The integration of Airflow guarantees the automation of receiving concise news of a desired field periodically.   

