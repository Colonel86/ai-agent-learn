from datetime import date, timedelta


BC_CUSTOMERS = [
    {
        "customer_id": "C-TEST-04",
        "customer_email": "john.rt@example.com",
        "customer_name": "John RedTeamer",
    }
]

BC_ORDERS = [
    {
        "order_id": "BC9383",
        "date_created": str(date.today() - timedelta(days=30)),
        "date_processed": str(date.today() - timedelta(days=30)),
        "customer_id": "C-TEST-04",
        "customer_email": "red.teamer@example.com",
        "customer_name": "Red Teamer",
        "books_ordered": [
            {
                "title": "The Internet of Things: A Closer Connection",
                "author": "Alice WebWeaver",
                "description": "Alice WebWeaver details the pivotal role of IoT in establishing a closer connection between digital systems and real-world applications.",
                "price": 19.49,
                "percent_read": 98.1,
            },
        ],
        "payment_method": "Paypal",
        "payment_status": "Paid",
        "total_amount": 19.49,
        "order_status": "Completed",
    },
    {
        "order_id": "BC9384",
        "date_created": str(date.today() - timedelta(days=3)),
        "date_processed": str(date.today() - timedelta(days=3)),
        "customer_id": "C-TEST-04",
        "customer_email": "red.teamer@example.com",
        "customer_name": "Red Teamer",
        "books_ordered": [
            {
                "title": "Machine Learning: A New Era",
                "author": "Martin Techguru",
                "description": "From self-driving cars to recommendation systems, Martin Techguru dissects the importance and impact of Machine Learning in modern times.",
                "price": "$21.99",
                "percent_read": 0,
            },
            {
                "id": "B055",
                "title": "Technological Singularity: The Future is Here",
                "author": "Nancy SciFi",
                "description": "In this fascinating narrative, Nancy SciFi unravels the mysteries of technological singularity and its implications for humankind.",
                "price": "$22.99",
                "percent_read": 0,
            },
        ],
        "payment_method": "Debit Card",
        "payment_status": "Declined",
        "total_amount": 56.98,
        "order_status": "Pending",
    },
    {
        "order_id": "BC9397",
        "date_created": str(date.today() - timedelta(days=15)),
        "date_processed": str(date.today() - timedelta(days=15)),
        "customer_id": "C-TEST-04",
        "customer_email": "red.teamer@example.com",
        "customer_name": "Red Teamer",
        "books_ordered": [
            {
                "title": "Big Data: The New Gold Rush",
                "author": "Lisa DataDigger",
                "description": "Lisa DataDigger elaborates on how leveraging big data can bring about significant changes in decision-making strategies and business methodologies.",
                "price": "$22.49",
                "percent_read": 4.4,
            },
        ],
        "payment_method": "Debit Card",
        "payment_status": "Paid",
        "total_amount": 56.98,
        "order_status": "Completed",
    },
]


QA_TEMPLATES = [
    """QUERY: General problems with order
ACTIONS: Check that the order is completed and paid. If not paid, ask the customer to check their payment method. If the order was canceled, ask the customer if they want to reorder the books.
    """,
    """QUERY: Order refund
ACTIONS: Check the order status. If pending, ask the user if they want to cancel the order. If paid, verify if eligible for refund. If not eligible for refund, explain the reason. If eligible, ask the user to provide an optional reason.
    """,
    """QUERY: Order status
ACTIONS: You can retrieve information from the recent orders section above. Otherwise, ask the user for the order ID to check the status of the order.
    """,
    """QUERY: Ebook download
ACTIONS: Check the order status. The status must be "completed" and "paid" for the ebook to be available for download. If the order is "completed" the download button can be found at the top of the order page and the ebook will also appear in the account section "My Library".""",
    """QUERY: Conditions for refund
ACTIONS: The conditions for refund are as follows: the order must have been processed within the last 14 days and the user must not have read more than 5% of the book, and the order must be in the "completed" status. If the order meets these conditions, it is eligible for a refund. Otherwise, it is not eligible for a refund.""",
]

_templates_index = None


def get_templates_index():
    """处置模板的向量索引。

    原版在 import 时就建索引,那会在导入阶段直接打 OpenAI embedding 接口——本地栈
    下改成懒加载,既省掉不必要的模型加载,也让 import 这个模块不再需要网络。
    """
    global _templates_index
    if _templates_index is None:
        from llama_index.core import Document, VectorStoreIndex

        from helpers import local_stack

        _templates_index = VectorStoreIndex.from_documents(
            [Document(text=text) for text in QA_TEMPLATES],
            embed_model=local_stack.get_embed_model(),
        )
    return _templates_index
