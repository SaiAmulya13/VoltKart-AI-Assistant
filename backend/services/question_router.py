
# ==========================================
# Question Router
# ==========================================


def identify_question_type(question):

    question = question.lower().strip()

    # --------------------------------------
    # 1. Document-related questions
    # --------------------------------------

    rag_keywords = [
        "policy",
        "return period",
        "return window",
        "return policy",
        "refund timeline",
        "refund processing",
        "warranty",
        "voltcare",
        "job description",
        "salary",
        "machine learning engineer",
        "restocking fee",
        "exchange",
        "business days",
        "working days",
        "store operations",
        "notice",
        "document",
        "terms and conditions"
    ]

    if any(keyword in question for keyword in rag_keywords):
        return "rag"

    # --------------------------------------
    # 2. Explicit uploaded CSV questions
    # --------------------------------------

    uploaded_csv_keywords = [
        "uploaded csv",
        "uploaded file",
        "uploaded dataset",
        "uploaded data",
        "this csv",
        "this file",
        "this dataset",
        "my csv",
        "my file",
        "in the csv",
        "from the csv",
        "in this csv",
        "in this file",
        "csv file",
        "csv data"
    ]

    if any(keyword in question for keyword in uploaded_csv_keywords):
        return "uploaded_csv"

    # --------------------------------------
    # 3. Multi-file analysis questions
    # --------------------------------------

    multi_file_keywords = [
        "which customers purchased",
        "which customer purchased",
        "customers purchased",
        "customer purchased",
        "purchase quantity",
        "total purchase quantity",
        "customer placed the most orders",
        "customers placed the most orders",
        "customer with the most orders",
        "customers with the most orders",
        "customers never placed",
        "customers without orders",
        "customers who never ordered",
        "product sold the highest quantity",
        "highest quantity sold",
        "total quantity sold",
        "quantity of products sold",
        "customer and order",
        "customers and orders",
        "orders and order items"
    ]

    if any(keyword in question for keyword in multi_file_keywords):
        return "uploaded_csv"

    # --------------------------------------
    # 4. General uploaded CSV analysis
    # --------------------------------------

    analysis_keywords = [
        "average",
        "mean",
        "total",
        "sum",
        "maximum",
        "minimum",
        "max",
        "min",
        "highest",
        "lowest",
        "largest",
        "smallest",
        "count",
        "how many",
        "number of rows",
        "number of records",
        "row count",
        "record count",
        "column names",
        "missing values",
        "missing data",
        "null values",
        "most common",
        "top",
        "bottom",
        "sort",
        "describe",
        "summary",
        "distribution"
    ]

    if any(keyword in question for keyword in analysis_keywords):
        return "uploaded_csv"

    # --------------------------------------
    # 5. Predefined VoltKart business questions
    # --------------------------------------

    csv_keywords = [
        "revenue",
        "sales",
        "store",
        "customer",
        "customers",
        "product",
        "products",
        "order",
        "orders",
        "purchased",
        "purchase",
        "top customer",
        "highest revenue",
        "most returned product",
        "refunds by region",
        "payment method",
        "quantity",
        "delivered",
        "cancelled"
    ]

    if any(keyword in question for keyword in csv_keywords):
        return "csv"

    # --------------------------------------
    # 6. Unknown question
    # --------------------------------------

    return "unknown"
