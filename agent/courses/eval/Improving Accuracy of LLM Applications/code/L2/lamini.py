class Lamini:
    def __init__(self, model_name):
        if model_name == "meta-llama/Meta-Llama-3-8B-Instruct":
            self.responses = {
                "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are an NBA analyst with 15 years of experience writing complex SQL queries. Consider the nba_roster table with the following schema:\n0|Team|TEXT \n1|NAME|TEXT  \n2|Jersey|TEXT \n3|POS|TEXT\n4|AGE|INT \n5|HT|TEXT \n6|WT|TEXT \n7|COLLEGE|TEXT \n8|SALARY|TEXT eg. \n\n\nWrite a sqlite query to answer the following question. Follow instructions exactly<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nWho is the highest paid NBA player?<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n": "To answer this question, we can use the following SQLite query:\n\n```sql\nSELECT NAME, SALARY\nFROM nba_roster\nORDER BY SALARY DESC\nLIMIT 1;\n```\n\nThis query will return the name and salary of the highest paid NBA player. The `ORDER BY SALARY DESC` clause sorts the players by their salary in descending order (highest to lowest), and the `LIMIT 1` clause ensures that we only get the top result.",
                '<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are an NBA analyst with 15 years of experience writing complex SQL queries. Consider the nba_roster table with the following schema:\n0|Team|TEXT eg. "Toronto Raptors"\n1|NAME|TEXT eg. "Otto Porter Jr."\n2|Jersey|TEXT eg. "0" and when null has a value "NA"\n3|POS|TEXT eg. "PF"\n4|AGE|INT eg. "22" in years\n5|HT|TEXT eg. `6\' 7"` or `6\' 10"`\n6|WT|TEXT eg. "232 lbs" \n7|COLLEGE|TEXT eg. "Michigan" and when null has a value "--"\n8|SALARY|TEXT eg. "$9,945,830" and when null has a value "--"\n\n\nWrite a sqlite query to answer the following question. Follow instructions exactly<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nWho is the highest paid NBA player?<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n': "To answer this question, we can use the following SQL query:\n\n```sql\nSELECT NAME, SALARY\nFROM nba_roster\nWHERE SALARY!= '--'\nORDER BY CAST(SALARY AS REAL) DESC\nLIMIT 1;\n```\n\nThis query first filters out the rows where the salary is '--' (i.e., the players who don't have a salary listed). Then, it orders the remaining rows by the salary in descending order (highest to lowest). Finally, it returns the top row, which corresponds to the highest paid NBA player.",
            }
            self.json_responses = {
                '<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are an NBA analyst with 15 years of experience writing complex SQL queries. Consider the nba_roster table with the following schema:\n0|Team|TEXT eg. "Toronto Raptors"\n1|NAME|TEXT eg. "Otto Porter Jr."\n2|Jersey|TEXT eg. "0" and when null has a value "NA"\n3|POS|TEXT eg. "PF"\n4|AGE|INT eg. "22" in years\n5|HT|TEXT eg. `6\' 7"` or `6\' 10"`\n6|WT|TEXT eg. "232 lbs" \n7|COLLEGE|TEXT eg. "Michigan" and when null has a value "--"\n8|SALARY|TEXT eg. "$9,945,830" and when null has a value "--"\n\n\nWrite a sqlite query to answer the following question. Follow instructions exactly<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nWho is the highest paid NBA player?<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n': {
                    "sqlite_query": "SELECT NAME, SALARY FROM nba_roster WHERE SALARY!= '--' ORDER BY CAST(SALARY AS REAL) DESC LIMIT 1"
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
        return self.responses.get(
            prompt,
            "Sorry, I don't know how to respond to that. Please stick to the notebook example.",
        )
