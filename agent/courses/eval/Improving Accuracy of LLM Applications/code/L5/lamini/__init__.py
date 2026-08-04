class Lamini:
    def __init__(self, model_name):
        if model_name == "meta-llama/Meta-Llama-3-8B-Instruct":
            self.responses = {"": ""}
            self.json_responses_sql_query = {
                '<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are an NBA analyst with 15 years of experience writing complex SQL queries.\nConsider a table called \'nba_roster\' with the following schema (columns)\n0|Team|TEXT eg. "Toronto Raptors"\n1|NAME|TEXT eg. "Otto Porter Jr."\n2|Jersey|TEXT eg. "0" and when null has a value "NA"\n3|POS|TEXT eg. "PF"\n4|AGE|INT eg. "22" in years\n5|HT|TEXT eg. `6\' 7"` or `6\' 10"` castable to int\n6|WT|TEXT eg. "232 lbs" \n7|COLLEGE|TEXT eg. "Michigan" and when null has a value "--"\n8|SALARY|TEXT eg. "$9,945,830" and when null has a value "--"\nConsider the following questions, and queries used to answer them:\nQuestion: What is the median weight in the NBA?\nQuery: select CAST(SUBSTR(WT, 1, INSTR(WT,\' \')) as INTEGER) as percentile from nba_roster order by percentile limit 1 offset (select count(*) from nba_roster)/2;\n<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nWrite two queries that are similar but different to those above.\nFormat the queries as a JSON object, i.e.\n{ "explanation": str, "sql_query_1" : str, "sql_query_2": str }.\nFirst write an explanation of why you decided to write these new queries in about 3-5 sentences, then write valid sqlite SQL queries for each of the 2 new queries. Make sure each query is complete and ends with a ;\n<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n': {
                    "explanation": "I decided to write these new queries to provide more insights into the NBA data. The first query calculates the average height of players in the NBA, while the second query finds the team with the highest average salary. These queries are similar to the original query in that they involve extracting and manipulating",
                    "sql_query_1": "SELECT AVG(CAST(SUBSTR(HT, 1, INSTR(HT,'')-1) AS INTEGER)) AS average_height FROM nba_roster",
                    "sql_query_2": "SELECT Team, AVG(CAST(SUBSTR(SALARY, 2, LENGTH(SALARY)-2) AS INTEGER)) AS average_salary FROM nba_roster WHERE SALARY!= '--' GROUP BY Team ORDER BY average_salary DESC LIMIT 1",
                }
            }
            self.json_responses_question = {
                '<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are an NBA analyst with 15 years of experience writing complex SQL queries.\nConsider a table called \'nba_roster\' with the following schema (columns)\n0|Team|TEXT eg. "Toronto Raptors"\n1|NAME|TEXT eg. "Otto Porter Jr."\n2|Jersey|TEXT eg. "0" and when null has a value "NA"\n3|POS|TEXT eg. "PF"\n4|AGE|INT eg. "22" in years\n5|HT|TEXT eg. `6\' 7"` or `6\' 10"`\n6|WT|TEXT eg. "232 lbs" \n7|COLLEGE|TEXT eg. "Michigan" and when null has a value "--"\n8|SALARY|TEXT eg. "$9,945,830" and when null has a value "--"\n\nQueries, and questions that they are used to answer:\nQuestion: What is the median weight in the NBA?\nQuery: select CAST(SUBSTR(WT, 1, INSTR(WT,\' \')) as INTEGER) as percentile from nba_roster order by percentile limit 1 offset (select count(*) from nba_roster)/2;\n<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nNow consider the following query.\nQuery: SELECT Team, AVG(CAST(SUBSTR(SALARY, 2, LENGTH(SALARY)-2) AS INTEGER)) AS average_salary FROM nba_roster WHERE SALARY!= \'--\' GROUP BY Team ORDER BY average_salary DESC LIMIT 1\nWrite a question that this query could be used to answer.\nFormat your response as a JSON object, i.e.\n{ "explanation": str, "question": str }.\nFirst write an explanation in about 3-5 sentences, then write a one sentence question.\n<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n': {
                    "explanation": "This query calculates the average salary for each team in the NBA, excluding teams with unknown salaries. It does this by first removing the dollar sign and any leading or trailing characters from the salary string, then converting the remaining characters to an integer. The results are then grouped by team and ordered in descending order by average salary, with the team having the highest average salary returned first. The LIMIT 1 clause ensures that only the top team is returned",
                    "question": "Which team has the highest average salary among all teams in the NBA",
                }
            }
        elif (
            model_name
            == "a5ebf1c4879569101f32444afae5adcafbfce9c5a6ed13035fd892147f7d59bc"
        ):
            self.responses = {
                '<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are an NBA analyst with 15 years of experience writing complex SQL queries. Consider the nba_roster table with the following schema:\n0|Team|TEXT eg. "Toronto Raptors"\n1|NAME|TEXT eg. "Otto Porter Jr."\n2|Jersey|TEXT eg. "0" and when null has a value "NA"\n3|POS|TEXT eg. "PF"\n4|AGE|INT eg. "22" in years\n5|HT|TEXT eg. `6\' 7"` or `6\' 10"`\n6|WT|TEXT eg. "232 lbs" \n7|COLLEGE|TEXT eg. "Michigan" and when null has a value "--"\n8|SALARY|TEXT eg. "$9,945,830" and when null has a value "--"\n\n\nWrite a sqlite query to answer the following question. Follow instructions exactly<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nWho is the highest paid NBA player?<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n': "select salary, name from nba_roster where SALARY!= '--' ORDER BY CAST(REPLACE(REPLACE(SALARY, '$', ''), ',','') AS INTEGER) DESC LIMIT 1"
            }
        elif (
            model_name
            == "63fd73a775daf24216b46c680a1e963a8d1e02b21bca43fcea6c26737d2e887e"
        ):
            self.responses = {
                '<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are an NBA analyst with 15 years of experience writing complex SQL queries. Consider the nba_roster table with the following schema:\n0|Team|TEXT eg. "Toronto Raptors"\n1|NAME|TEXT eg. "Otto Porter Jr."\n2|Jersey|TEXT eg. "0" and when null has a value "NA"\n3|POS|TEXT eg. "PF"\n4|AGE|INT eg. "22" in years\n5|HT|TEXT eg. `6\' 7"` or `6\' 10"`\n6|WT|TEXT eg. "232 lbs" \n7|COLLEGE|TEXT eg. "Michigan" and when null has a value "--"\n8|SALARY|TEXT eg. "$9,945,830" and when null has a value "--"\n\n\nWrite a sqlite query to answer the following question. Follow instructions exactly<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nWhat is the median age of the Chicago Bulls?<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n': "SELECT CAST(AGE AS INTEGER) AS percentile FROM nba_roster WHERE team='Chicago Bulls' ORDER BY percentile LIMIT 1 OFFSET (SELECT COUNT(*) FROM nba_roster WHERE team='Chicago Bulls')/2;"
            }
        else:
            raise ValueError("Invalid model. Please stick to the notebook example.")

    def generate(self, prompt, max_new_tokens=100, output_type={}):
        if output_type == {
            "explanation": "str",
            "sql_query_1": "str",
            "sql_query_2": "str",
        }:
            return self.json_responses_sql_query.get(
                prompt,
                "Sorry, I don't know how to respond to that. Please stick to the notebook example.",
            )
        elif output_type == {"explanation": "str", "question": "str"}:
            return self.json_responses_question.get(
                prompt,
                "Sorry, I don't know how to respond to that. Please stick to the notebook example.",
            )
        else:
            return self.responses.get(
                prompt,
                "Sorry, I don't know how to respond to that. Please stick to the notebook example.",
            )
