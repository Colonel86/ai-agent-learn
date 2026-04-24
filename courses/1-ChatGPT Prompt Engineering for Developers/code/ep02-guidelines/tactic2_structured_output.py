"""
Tactic 2: Ask for a structured output
策略二：要求结构化输出（JSON / HTML）

演示：
  A. 生成 JSON 并用 Python 解析
  B. 生成 HTML 表格
"""
import json
from config import get_completion, print_section


def demo_json():
    """要求 JSON 格式输出，并验证可被 Python 直接解析。"""
    print_section("A. JSON 输出 + Python 解析")

    prompt = """
Generate a list of three made-up book titles along \
with their authors and genres.
Provide them in JSON format with the following keys:
book_id, title, author, genre.
"""
    response = get_completion(prompt)
    print(f"[Raw Response]\n{response}\n")

    # 验证：直接解析成 Python 对象
    try:
        books = json.loads(response)
        print("[Parsed as Python list]")
        for book in books:
            print(f"  #{book['book_id']} 《{book['title']}》 by {book['author']} [{book['genre']}]")
    except json.JSONDecodeError as e:
        print(f"[解析失败] {e}")
        print("提示：模型有时会在 JSON 外面包一层 markdown 代码块，需要先去掉 ```json ... ```")


def demo_html():
    """要求 HTML 表格输出。"""
    print_section("B. HTML 表格输出")

    data = {
        "employees": [
            {"name": "Alice", "role": "Engineer", "email": "alice@example.com"},
            {"name": "Bob",   "role": "Designer", "email": "bob@example.com"},
            {"name": "Carol", "role": "PM",        "email": "carol@example.com"},
        ]
    }

    prompt = f"""
Convert the following Python dictionary to an HTML table \
with column headers and a title row.
{data}
"""
    response = get_completion(prompt)
    print(f"[HTML Output]\n{response}")

    # 可选：把 HTML 写到文件里，用浏览器打开看效果
    with open("output_table.html", "w") as f:
        f.write(response)
    print("\n[已保存到 output_table.html，用浏览器打开可预览]")


# ── 自由练习区 ───────────────────────────────────────────────────────────────
def your_turn():
    """
    TODO: 修改 prompt，要求模型输出其他格式（比如 CSV、Markdown 表格）
    或者换一个领域（比如生成 5 部电影的 JSON）。
    """
    print_section("C. 自由练习")

    prompt = """
Generate a list of 3 movies with their directors and release years.
Return as JSON with keys: movie_id, title, director, year.
"""  # ← 修改这里
    response = get_completion(prompt)
    print(f"[Response]\n{response}")


if __name__ == "__main__":
    demo_json()
    demo_html()
    # your_turn()
