
# ==========================================
# Question Router
# ==========================================


def identify_question_type(question):

    question = question.lower().strip()

    # --------------------------------------
    # 1. Hybrid questions
    # These require both CSV and documents
    # --------------------------------------

    combined_keywords = [

        "does the order data agree",
        "does the data agree",
        "according to the order data",
        "according to the store notice",
        "according to the uploaded data",
        "according to the csv and",
        "store was closed",
        "closed in december",
        "within the window",
        "if it were within",
        "would a restocking fee",
        "is that allowed",
        "was the order placed during",
        "compare the order data with",
        "compare the csv with the notice",
        "compare the data with the policy",
        "based on the order data and policy",
    ]

    if any(keyword in question for keyword in combined_keywords):
        return "hybrid"

    # --------------------------------------
    # 2. Document-related questions
    # --------------------------------------

    rag_keywords = [

        # Return and refund policy
        "return period",
        "return window",
        "return policy",
        "returnable",
        "return within",
        "refund timeline",
        "refund processing",
        "refund takes",
        "refund take",
        "refund time",
        "restocking fee",
        "return fee",
        "exchange",
        "gold members",
        "platinum members",

        # Damaged or defective products
        "damaged on delivery",
        "damage on delivery",
        "damaged product",
        "product damaged",
        "report damage",
        "report a damage",
        "report a damaged",
        "defective product",
        "defective item",
        "opened earbuds",
        "opened earbud",
        "earbuds returnable",
        "earbud returnable",

        # Warranty
        "warranty",
        "voltcare",
        "warranty claim",
        "number of claims",
        "claim limit",

        # Job description
        "job description",
        "machine learning engineer",
        "salary range",
        "work mode",
        "job location",
        "reports to",
        "reporting manager",

        # Document and notice questions
        "business days",
        "working days",
        "store operations notice",
        "operations notice",
        "store notice",
        "terms and conditions",

        # Common document question wording
        "how soon must",
        "how soon should",
        "how long does",
        "how long will",
        "how many days does",
        "how many business days",
        "is it allowed",
        "is it eligible",
        "are opened",
        "can i return",
        "can this be returned",
        "according to the policy",
        "according to the document",
        "according to the notice",
    ]

    if any(keyword in question for keyword in rag_keywords):
        return "rag"

    # --------------------------------------
    # 3. Explicit uploaded CSV questions
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
        "csv data",
    ]

    if any(keyword in question for keyword in uploaded_csv_keywords):
        return "uploaded_csv"

    # --------------------------------------
    # 4. Multi-file analysis questions
    # --------------------------------------

    multi_file_keywords = [

        # Customer and order analysis
        "which customers purchased",
        "which customer purchased",
        "customers purchased",
        "customer purchased",
        "customer and order",
        "customers and orders",
        "orders and order items",
        "customer placed the most orders",
        "customers placed the most orders",
        "customer with the most orders",
        "customers with the most orders",
        "customers never placed",
        "customers without orders",
        "customers who never ordered",

        # Purchase quantity
        "purchase quantity",
        "total purchase quantity",
        "product sold the highest quantity",
        "highest quantity sold",
        "total quantity sold",
        "quantity of products sold",

        # Customer spending
        "top 3 customers",
        "top three customers",
        "customers by spend",
        "customers by spending",
        "customer spend",
        "customer spending",
        "spent the most at",
        "spending at the same store",
        "customer spend at",
        "customer spending at",
        "at that store",

        # Store revenue and manager
        "store with the highest revenue",
        "highest revenue store",
        "store generated the most revenue",
        "store manager",
        "manager of the store",
        "revenue generated by each store",

        # Customer city and product filters
        "customers whose home city",
        "home city is bengaluru",
        "bengaluru customers",
        "platinum customers",
        "platinum customer",
        "bought a laptop",
        "purchased a laptop",
        "purchased laptops",
        "laptop purchases",
        "first quarter of 2026",
        "q1 2026",

        # Return analysis
        "most common return reason",
        "returned most often",
        "most returned product",
        "most frequently returned product",
        "product returned the most",
        "common return reason",
        "return reason for",
        "return frequency",

        # Refund analysis
        "refund amount by region",
        "refunds by region",
        "total refund amount by region",
        "refunds by store region",
        "refund amount for each region",

        # Product category revenue
        "revenue by product category",
        "category revenue",
        "sales by product category",

        # Monthly sales
        "units sold per month",
        "smartphone units sold",
        "smartphones sold per month",
        "monthly smartphone sales",
        "monthly units sold",
        "monthly sales",

    ]

    if any(keyword in question for keyword in multi_file_keywords):
        return "csv"

    # --------------------------------------
    # 5. General CSV analysis questions
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
        "distribution",

    ]

    if any(keyword in question for keyword in analysis_keywords):
        return "uploaded_csv"

    # --------------------------------------
    # 6. Predefined VoltKart business questions
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
        "highest revenue",
        "most returned product",
        "refunds by region",
        "refund amount",
        "payment method",
        "quantity",
        "delivered",
        "cancelled",
        "return reason",
        "return status",
        "store manager",
        "store closure",
        "store closed",
        "bengaluru",
        "platinum customer",
        "laptop",
        "smartphone",
        "region",

    ]

    if any(keyword in question for keyword in csv_keywords):
        return "csv"

    # --------------------------------------
    # 7. Unknown question
    # --------------------------------------

    return "unknown"
