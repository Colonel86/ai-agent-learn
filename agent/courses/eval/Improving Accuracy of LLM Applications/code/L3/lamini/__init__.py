class Lamini:
    def __init__(self, model_name):
        if model_name == "meta-llama/Meta-Llama-3-8B-Instruct":
            self.responses = {"": ""}
            self.json_responses = {
                '<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are an NBA analyst with 15 years of experience writing complex SQL queries. Consider the nba_roster table with the following schema:\n0|Team|TEXT eg. "Toronto Raptors"\n1|NAME|TEXT eg. "Otto Porter Jr."\n2|Jersey|TEXT eg. "0" and when null has a value "NA"\n3|POS|TEXT eg. "PF"\n4|AGE|INT eg. "22" in years\n5|HT|TEXT eg. `6\' 7"` or `6\' 10"`\n6|WT|TEXT eg. "232 lbs" \n7|COLLEGE|TEXT eg. "Michigan" and when null has a value "--"\n8|SALARY|TEXT eg. "$9,945,830" and when null has a value "--"\n\n\nWrite a sqlite query to answer the following question. Follow instructions exactly<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nWhat is the median weight in the NBA?<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n': {
                    "sqlite_query": "SELECT AVG(CAST(SUBSTR(WT, INSTR(WT,'') + 1) AS INTEGER) FROM nba_roster WHERE WT IS NOT NULL"
                },
                '<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are an NBA analyst with 15 years of experience writing complex SQL queries. Consider the nba_roster table with the following schema:\n0|Team|TEXT eg. "Toronto Raptors"\n1|NAME|TEXT eg. "Otto Porter Jr."\n2|Jersey|TEXT eg. "0" and when null has a value "NA"\n3|POS|TEXT eg. "PF"\n4|AGE|INT eg. "22" in years\n5|HT|TEXT eg. `6\' 7"` or `6\' 10"`\n6|WT|TEXT eg. "232 lbs" \n7|COLLEGE|TEXT eg. "Michigan" and when null has a value "--"\n8|SALARY|TEXT eg. "$9,945,830" and when null has a value "--"\n\n\nWrite a sqlite query to answer the following question. Follow instructions exactly<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nQuestion: What is the median weight in the NBA?. Query: SELECT AVG(CAST(SUBSTR(WT, INSTR(WT,\'\') + 1) AS INTEGER) FROM nba_roster WHERE WT IS NOT NULL. This query is invalid (gets the error Execution failed on sql \'SELECT AVG(CAST(SUBSTR(WT, INSTR(WT,\'\') + 1) AS INTEGER) FROM nba_roster WHERE WT IS NOT NULL\': near "FROM": syntax error), so it cannot answer the question. Write a corrected sqlite query.<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n': {
                    "sqlite_query": "SELECT AVG(CAST(SUBSTR(WT, INSTR(WT,'') + 1) AS INTEGER) FROM nba_roster WHERE WT IS NOT NULL"
                },
                '<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are an NBA analyst with 15 years of experience writing complex SQL queries.\nConsider the nba_roster table with the following schema:\n0|Team|TEXT eg. "Toronto Raptors"\n1|NAME|TEXT eg. "Otto Porter Jr."\n2|Jersey|TEXT eg. "0" and when null has a value "NA"\n3|POS|TEXT eg. "PF"\n4|AGE|INT eg. "22" in years\n5|HT|TEXT eg. `6\' 7"` or `6\' 10"`\n6|WT|TEXT eg. "232 lbs" \n7|COLLEGE|TEXT eg. "Michigan" and when null has a value "--"\n8|SALARY|TEXT eg. "$9,945,830" and when null has a value "--"\n\nWrite a sqlite SQL query that would help you answer the following question:\n<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nCan you tell me how many players are in the NBA?<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n': {
                    "sqlite_query": "SELECT COUNT(*) FROM nba_roster WHERE Jersey!= 'NA';"
                },
            }
            self.json_responses_similarity = {
                "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nCompare the following two dataframes. They are similar if they are almost identical, or if they convey the same information about the nba_roster datasetRespond with valid JSON {'explanation' : str, 'similar' : bool}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n========== Dataframe 1 =========\n   count(*)\n0       476\n\n========== Dataframe 2 =========\n   count(*)\n0       600\n\nCan you tell me if these dataframes are similar?<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n": {
                    "explanation": "The dataframes are not similar because they have different counts. The first dataframe has a count of 476, while the second dataframe has a count of 600",
                    "similar": False,
                }
            }
        else:
            raise ValueError("Invalid model. Please stick to the notebook example.")

    def generate(self, prompt, max_new_tokens=100, output_type={}):
        if output_type == {"sqlite_query": "str"}:
            return self.json_responses.get(
                prompt,
                "Sorry, I don't know how to respond to that. Please stick to the notebook example.",
            )
        elif output_type == {"explanation": "str", "similar": "bool"}:
            return self.json_responses_similarity.get(
                prompt,
                "Sorry, I don't know how to respond to that. Please stick to the notebook example.",
            )
        else:
            return self.responses.get(
                prompt,
                "Sorry, I don't know how to respond to that. Please stick to the notebook example.",
            )
