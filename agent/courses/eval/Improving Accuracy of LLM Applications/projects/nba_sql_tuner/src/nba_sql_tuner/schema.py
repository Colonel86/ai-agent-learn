"""NBA roster 表结构描述 —— 对应课程 util/get_schema.py。

课程里 L2 的一个关键教学点:第一版 schema(get_schema)信息太少,模型不知道
SALARY 是 `$9,945,830` 这种带 $ 和逗号的字符串,于是生成 `CAST(SALARY AS REAL)`
这种错查询 → 幻觉。补上「示例值 + null 表示」的第二版(get_updated_schema)后,
模型才知道要 REPLACE 掉 $ 和逗号再 CAST。所以这里两版都保留。
"""


def get_schema() -> str:
    """信息贫乏版:只有列名和类型。复现「模型不知道字符串格式 → 生成错 SQL」。"""
    return """\
0|Team|TEXT
1|NAME|TEXT
2|Jersey|TEXT
3|POS|TEXT
4|AGE|INT
5|HT|TEXT
6|WT|TEXT
7|COLLEGE|TEXT
8|SALARY|TEXT
"""


def get_updated_schema() -> str:
    """信息丰富版:每列带示例值和 null 表示。这是 SQL Agent 实际该用的。"""
    return """\
0|Team|TEXT eg. "Toronto Raptors"
1|NAME|TEXT eg. "Otto Porter Jr."
2|Jersey|TEXT eg. "0" and when null has a value "NA"
3|POS|TEXT eg. "PF"
4|AGE|INT eg. "22" in years
5|HT|TEXT eg. `6' 7"` or `6' 10"`
6|WT|TEXT eg. "232 lbs"
7|COLLEGE|TEXT eg. "Michigan" and when null has a value "--"
8|SALARY|TEXT eg. "$9,945,830" and when null has a value "--"
"""


def get_schema_s() -> str:
    """单行紧凑版 —— 对应课程 get_schema_s,用于 L5 生成数据时省 token。"""
    return (
        "Team, NAME, Jersey, POS, AGE, HT, WT, COLLEGE, SALARY. "
        'SALARY is text like "$9,945,830" (null="--"); '
        'WT is text like "232 lbs"; HT is text like `6\' 7"`; '
        'Jersey null="NA"; COLLEGE null="--".\n'
    )
