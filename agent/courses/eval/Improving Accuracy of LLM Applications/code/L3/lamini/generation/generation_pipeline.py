class GenerationPipeline:
    def __init__(self):
        pass

    def call(self, dataset):
        import pandas as pd
        import sqlite3
        import jsonlines
        import logging

        logger = logging.getLogger(__name__)

        with jsonlines.open("data/results/nba_sql_pipeline/sql_errors.jsonl") as reader:
            data_list = [obj for obj in reader]

        with jsonlines.open(
            "data/results/nba_sql_pipeline/sql_results.jsonl"
        ) as reader:
            data_list.extend(obj for obj in reader)

        engine = sqlite3.connect("./nba_roster.db")

        for data in data_list:
            try:
                logger.info(f"Running reference SQL query '{data['query']}'")
                df = pd.read_sql(data["query"], con=engine)
                logger.info(f"Got data: {df}")

                logger.info(f"For question: {data['question']}")
                logger.info(f"For query: {data['query']}")
            except:
                logger.error(f"Failed to run SQL query: {data['query']}")

        file_name = f"data/results/nba_sql_pipeline/summary.txt"

        average_sql_succeeded = sum(
            [data["query_succeeded"] for data in data_list]
        ) / len(data_list)
        average_correct = sum(
            [data["query_succeeded"] and data["is_matching"] for data in data_list]
        ) / len(data_list)

        with open(file_name, "r") as reader:
            print(f"\nTotal size of eval dataset: {len(data_list)}")
            print(f"Percent Valid SQL Syntax: {average_sql_succeeded*100}")
            print(f"Percent Correct SQL Query: {average_correct*100}")

        return data_list
