
import re
import pandas as pd

from backend.services.csv_service import load_csv_tables


def calculate_line_amount(df):

    """
    Calculate actual sales after discount.
    """

    return (
        df["quantity"]
        * df["unit_price_inr"]
        * (1 - df["discount_pct"] / 100)
    )


def prepare_sales_data(tables):

    """
    Join orders, order items, products,
    customers and stores.
    """

    orders = tables["orders"].copy()
    items = tables["order_items"].copy()

    orders["order_date"] = pd.to_datetime(
        orders["order_date"],
        errors="coerce"
    )

    sales = orders.merge(
        items,
        on="order_id",
        how="inner"
    )

    sales["line_amount"] = calculate_line_amount(sales)

    return sales


def build_citation(table_names, computation, result_context=None):

    citation = {
        "type": "table",
        "tables": table_names,
        "computation": computation
    }

    if result_context:
        citation["result_context"] = result_context

    return [citation]


def answer_highest_revenue(tables):

    sales = prepare_sales_data(tables)

    stores = tables["stores"].copy()

    # Only delivered orders from 2025
    sales = sales[
        (sales["order_status"] == "Delivered")
        & (sales["order_date"].dt.year == 2025)
    ]

    # Join store details
    sales = sales.merge(
        stores,
        on="store_id",
        how="inner"
    )

    # Calculate revenue by store
    revenue = sales.groupby(
        [
            "store_id",
            "store_name",
            "store_manager"
        ],
        as_index=False
    )["line_amount"].sum()

    # Sort highest revenue first
    revenue = revenue.sort_values(
        "line_amount",
        ascending=False
    )

    if revenue.empty:
        return {
            "answer": "No delivered sales records were found for 2025.",
            "citations": build_citation(
                ["orders.csv", "order_items.csv", "stores.csv"],
                "Filtered delivered orders in 2025."
            )
        }

    winner = revenue.iloc[0]

    answer = (
        f"The highest revenue store in 2025 was "
        f"{winner['store_name']} ({winner['store_id']}), "
        f"managed by {winner['store_manager']}. "
        f"Its total revenue was "
        f"₹{winner['line_amount']:,.2f}."
    )

    return {
        "answer": answer,
        "citations": build_citation(
            [
                "orders.csv",
                "order_items.csv",
                "stores.csv"
            ],
            (
                "Joined orders with order_items using order_id; "
                "filtered order_status = Delivered and year(order_date) = 2025; "
                "calculated quantity * unit_price_inr * "
                "(1 - discount_pct / 100); grouped by store "
                "and summed line_amount; sorted descending."
            ),
            {
                "store_id": winner["store_id"],
                "store_name": winner["store_name"]
            }
        )
    }


def answer_top_customers(tables, chat_history=None):

    sales = prepare_sales_data(tables)

    customers = tables["customers"].copy()
    stores = tables["stores"].copy()

    # Get previous store from conversation
    previous_store_id = None

    if chat_history:

        for message in reversed(chat_history):

            if message["role"] != "assistant":
                continue

            citations = message.get("citations", [])

            if isinstance(citations, str):
                import json
                citations = json.loads(citations or "[]")

            for citation in citations:

                context = citation.get("result_context", {})

                if context.get("store_id"):
                    previous_store_id = context["store_id"]
                    break

            if previous_store_id:
                break

    # Fallback: calculate highest-revenue store
    # if this is not a follow-up question.
    if not previous_store_id:

        previous_result = answer_highest_revenue(tables)

        for citation in previous_result["citations"]:
            context = citation.get("result_context", {})
            previous_store_id = context.get("store_id")

    if not previous_store_id:

        return {
            "answer": "I could not identify the store for this question.",
            "citations": []
        }

    # Filter 2025 delivered orders
    sales = sales[
        (sales["order_status"] == "Delivered")
        & (sales["order_date"].dt.year == 2025)
        & (sales["store_id"] == previous_store_id)
    ]

    # Join customer details
    sales = sales.merge(
        customers,
        on="customer_id",
        how="inner"
    )

    # Calculate customer spending
    customer_spend = sales.groupby(
        ["customer_id", "full_name"],
        as_index=False
    )["line_amount"].sum()

    top_customers = customer_spend.sort_values(
        "line_amount",
        ascending=False
    ).head(3)

    if top_customers.empty:

        return {
            "answer": "No customer spending records were found for this store.",
            "citations": []
        }

    lines = []

    for index, row in enumerate(
        top_customers.itertuples(index=False),
        start=1
    ):

        lines.append(
            f"{index}. {row.full_name} "
            f"({row.customer_id}) – ₹{row.line_amount:,.2f}"
        )

    answer = (
        f"The top 3 customers at store {previous_store_id} "
        f"by spend in 2025 were:\n"
        + "\n".join(lines)
    )

    return {
        "answer": answer,
        "citations": build_citation(
            [
                "orders.csv",
                "order_items.csv",
                "customers.csv",
                "stores.csv"
            ],
            (
                "Used the store identified in the previous answer; "
                "filtered delivered orders in 2025; joined customers; "
                "calculated discounted line amounts; grouped by customer; "
                "sorted spending descending and selected the top 3."
            ),
            {"store_id": previous_store_id}
        )
    }


def answer_most_returned_product(tables):

    returns = tables["returns"].copy()
    items = tables["order_items"].copy()
    products = tables["products"].copy()

    # Connect returns with purchased products
    data = returns.merge(
        items,
        on="order_item_id",
        how="inner"
    )

    data = data.merge(
        products,
        on="product_id",
        how="inner"
    )

    # Count returns for every product
    product_counts = data.groupby(
        "product_name"
    ).size().sort_values(ascending=False)

    if product_counts.empty:

        return {
            "answer": "No return records were found.",
            "citations": []
        }

    product_name = product_counts.index[0]
    return_count = int(product_counts.iloc[0])

    # Find most common reason for this product
    reasons = data[
        data["product_name"] == product_name
    ]["return_reason"].value_counts()

    most_common_reason = reasons.index[0]
    reason_count = int(reasons.iloc[0])

    answer = (
        f"The most frequently returned product was "
        f"{product_name}, with {return_count} returns. "
        f"Its most common return reason was "
        f"'{most_common_reason}', recorded {reason_count} times."
    )

    return {
        "answer": answer,
        "citations": build_citation(
            [
                "returns.csv",
                "order_items.csv",
                "products.csv"
            ],
            (
                "Joined returns with order_items using order_item_id "
                "and products using product_id; counted returns by "
                "product_name; selected the highest count; calculated "
                "the most frequent return_reason for that product."
            )
        )
    }


def answer_platinum_laptop_customers(tables):

    customers = tables["customers"].copy()
    orders = tables["orders"].copy()
    items = tables["order_items"].copy()
    products = tables["products"].copy()

    orders["order_date"] = pd.to_datetime(
        orders["order_date"],
        errors="coerce"
    )

    # Connect all four tables
    data = orders.merge(
        customers,
        on="customer_id",
        how="inner"
    )

    data = data.merge(
        items,
        on="order_id",
        how="inner"
    )

    data = data.merge(
        products,
        on="product_id",
        how="inner"
    )

    # Q1 2026 = January 1 to March 31
    filtered = data[
        (data["loyalty_tier"] == "Platinum")
        & (data["home_city"].str.casefold() == "bengaluru")
        & (data["order_date"] >= "2026-01-01")
        & (data["order_date"] < "2026-04-01")
        & (data["category"].str.contains(
            "laptop",
            case=False,
            na=False
        ))
        & (data["order_status"] == "Delivered")
    ]

    # Count unique customers, not purchased units
    result = filtered[
        ["customer_id", "full_name"]
    ].drop_duplicates()

    names = result["full_name"].tolist()

    if not names:
        answer = (
            "No Platinum customers from Bengaluru "
            "who bought laptops in Q1 2026 were found."
        )

    else:
        answer = (
            f"{len(names)} Platinum customer(s) from Bengaluru "
            f"bought laptops in Q1 2026: "
            + ", ".join(names)
            + "."
        )

    return {
        "answer": answer,
        "citations": build_citation(
            [
                "customers.csv",
                "orders.csv",
                "order_items.csv",
                "products.csv"
            ],
            (
                "Joined customers, orders, order_items and products; "
                "filtered loyalty_tier = Platinum, home_city = Bengaluru, "
                "delivered orders dated 2026-01-01 through 2026-03-31, "
                "and product category containing laptop; counted "
                "distinct customer IDs."
            )
        )
    }


def answer_refunds_by_region(tables):

    returns = tables["returns"].copy()
    items = tables["order_items"].copy()
    orders = tables["orders"].copy()
    stores = tables["stores"].copy()

    # Join returns with order items
    data = returns.merge(
        items,
        on="order_item_id",
        how="inner"
    )

    # Join orders
    data = data.merge(
        orders,
        on="order_id",
        how="inner"
    )

    # Join store regions
    data = data.merge(
        stores,
        on="store_id",
        how="inner"
    )

    # Sum refunds by region
    refund_summary = data.groupby(
        "region"
    )["refund_amount_inr"].sum().sort_index()

    lines = []

    for region, amount in refund_summary.items():

        lines.append(
            f"{region}: ₹{amount:,.2f}"
        )

    answer = (
        "Total refund amount by region:\n"
        + "\n".join(lines)
    )

    return {
        "answer": answer,
        "citations": build_citation(
            [
                "returns.csv",
                "order_items.csv",
                "orders.csv",
                "stores.csv"
            ],
            (
                "Joined returns to order_items using order_item_id, "
                "to orders using order_id, and to stores using store_id; "
                "grouped refund_amount_inr by region and summed it."
            )
        )
    }


def answer_question(question, chat_history=None):

    """
    Route the question to the appropriate
    Pandas calculation function.
    """

    tables = load_csv_tables()

    q = re.sub(r"\s+", " ", question.lower()).strip()

    # Question 2: Follow-up about customers
    if (
        "top 3 customers" in q
        or "top three customers" in q
        or (
            "customers" in q
            and ("spend" in q or "spent" in q)
            and "store" in q
        )
    ):

        return answer_top_customers(
            tables,
            chat_history
        )

    # Question 1: Store revenue
    if (
        "highest revenue" in q
        or "highest sales" in q
        or (
            "store" in q
            and "revenue" in q
        )
    ):

        return answer_highest_revenue(tables)

    # Question 3: Product returns
    if (
        "returned most often" in q
        or "most returned product" in q
        or (
            "return" in q
            and "product" in q
            and "reason" in q
        )
    ):

        return answer_most_returned_product(tables)

    # Question 4: Platinum laptop customers
    if (
        "platinum" in q
        and "bengaluru" in q
        and "laptop" in q
    ):

        return answer_platinum_laptop_customers(tables)

    # Question 5: Refunds by region
    if (
        "refund" in q
        and "region" in q
    ):

        return answer_refunds_by_region(tables)

    return {
        "answer": (
            "I could not identify a supported table question. "
            "Please ask about store revenue, top customers, "
            "returned products, Platinum laptop customers "
            "or refunds by region."
        ),
        "citations": []
    }
