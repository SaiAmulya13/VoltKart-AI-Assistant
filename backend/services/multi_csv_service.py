
from pathlib import Path
import re

import pandas as pd


# -----------------------------------------
# Project paths
# -----------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TABLES_FOLDER = PROJECT_ROOT / "data" / "tables"


# -----------------------------------------
# Expected CSV files
# -----------------------------------------

TABLE_FILES = {
    "customers": "customers.csv",
    "orders": "orders.csv",
    "order_items": "order_items.csv",
    "products": "products.csv",
    "returns": "returns.csv",
    "stores": "stores.csv",
}


# -----------------------------------------
# Load CSV tables
# -----------------------------------------

def load_multi_csv_tables():
    """
    Load all six main VoltKart CSV tables.
    """

    tables = {}

    for table_name, filename in TABLE_FILES.items():
        file_path = TABLES_FOLDER / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Required CSV file not found: {file_path}"
            )

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(
                f"Could not read {filename}: {e}"
            )

        tables[table_name] = df

    return tables


# -----------------------------------------
# Check required columns
# -----------------------------------------

def check_required_columns(
    df,
    required_columns,
    table_name
):
    """
    Check whether a table contains required columns.
    """

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{table_name} is missing columns: "
            f"{missing_columns}"
        )


# -----------------------------------------
# Build joined dataset
# -----------------------------------------

def build_multi_csv_dataset():
    """
    Join related VoltKart CSV tables.

    Relationships:
    customers.customer_id -> orders.customer_id
    stores.store_id -> orders.store_id
    orders.order_id -> order_items.order_id
    products.product_id -> order_items.product_id
    order_items.order_item_id -> returns.order_item_id
    """

    tables = load_multi_csv_tables()

    customers = tables["customers"].copy()
    orders = tables["orders"].copy()
    order_items = tables["order_items"].copy()
    products = tables["products"].copy()
    returns = tables["returns"].copy()
    stores = tables["stores"].copy()

    # Check join columns

    check_required_columns(
        customers,
        ["customer_id"],
        "customers"
    )

    check_required_columns(
        orders,
        [
            "order_id",
            "customer_id",
            "store_id",
            "order_date",
        ],
        "orders"
    )

    check_required_columns(
        order_items,
        [
            "order_item_id",
            "order_id",
            "product_id",
            "quantity",
            "unit_price_inr",
            "discount_pct",
        ],
        "order_items"
    )

    check_required_columns(
        products,
        ["product_id"],
        "products"
    )

    check_required_columns(
        stores,
        ["store_id"],
        "stores"
    )

    check_required_columns(
        returns,
        [
            "order_item_id",
            "refund_amount_inr",
            "return_id",
        ],
        "returns"
    )

    # Step 1: Join orders with customers

    dataset = orders.merge(
        customers,
        on="customer_id",
        how="left"
    )

    # Step 2: Join orders with stores

    dataset = dataset.merge(
        stores,
        on="store_id",
        how="left",
        suffixes=("", "_store")
    )

    # Step 3: Join orders with order items

    dataset = dataset.merge(
        order_items,
        on="order_id",
        how="left"
    )

    # Step 4: Join order items with products

    dataset = dataset.merge(
        products,
        on="product_id",
        how="left",
        suffixes=("", "_product")
    )

    # Step 5: Aggregate return information
    # Prevent duplicate order-item rows.

    returns_summary = (
        returns
        .groupby("order_item_id", as_index=False)
        .agg(
            refund_amount_inr=(
                "refund_amount_inr",
                "sum"
            ),
            return_count=(
                "return_id",
                "count"
            )
        )
    )

    dataset = dataset.merge(
        returns_summary,
        on="order_item_id",
        how="left",
        suffixes=("", "_return")
    )

    # Step 6: Clean numeric columns

    numeric_columns = [
        "quantity",
        "unit_price_inr",
        "discount_pct",
        "refund_amount_inr",
    ]

    for column in numeric_columns:
        dataset[column] = pd.to_numeric(
            dataset[column],
            errors="coerce"
        ).fillna(0)

    dataset["return_count"] = (
        dataset["return_count"]
        .fillna(0)
        .astype(int)
    )

    # Step 7: Calculate revenue

    dataset["gross_revenue_inr"] = (
        dataset["quantity"]
        * dataset["unit_price_inr"]
    )

    dataset["net_revenue_inr"] = (
        dataset["gross_revenue_inr"]
        * (1 - dataset["discount_pct"] / 100)
    )

    # Step 8: Add return indicator

    dataset["is_returned"] = (
        dataset["return_count"] > 0
    )

    return dataset


# -----------------------------------------
# Answer multi-CSV questions
# -----------------------------------------

def answer_multi_csv_question(question):
    """
    Answer supported questions requiring
    multiple VoltKart CSV tables.
    """

    dataset = build_multi_csv_dataset()

    question_lower = question.lower()

    # -----------------------------------------
    # Prepare dates
    # -----------------------------------------

    dataset["order_date"] = pd.to_datetime(
        dataset["order_date"],
        errors="coerce"
    )

    valid_dates = dataset[
        dataset["order_date"].notna()
    ].copy()

    year_match = re.search(
        r"\b(20\d{2})\b",
        question_lower
    )

    # -----------------------------------------
    # Month names
    # -----------------------------------------

    month_names = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    selected_month = None
    selected_month_name = None

    for month_name, month_number in month_names.items():
        if re.search(
            rf"\b{month_name}\b",
            question_lower
        ):
            selected_month = month_number
            selected_month_name = month_name.capitalize()
            break

    # -----------------------------------------
    # Order-specific lookup
    # -----------------------------------------
    # Example:
    # Show me the details of order O00174.
    # -----------------------------------------

    order_match = re.search(
        r"\bO\d{5}\b",
        question,
        re.IGNORECASE
    )

    if order_match:
        order_id = order_match.group(0).upper()

        order_data = dataset[
            dataset["order_id"]
            .astype(str)
            .str.upper()
            == order_id
        ].copy()

        if order_data.empty:
            return {
                "answer": (
                    f"I could not find order {order_id} "
                    "in the uploaded order data."
                ),
                "sources": [
                    "orders.csv",
                    "customers.csv",
                    "order_items.csv",
                    "products.csv",
                ],
            }

        # Customer information

        customer_name = (
            order_data["full_name"].iloc[0]
            if "full_name" in order_data.columns
            else "Unknown customer"
        )

        customer_city = (
            order_data["home_city"].iloc[0]
            if "home_city" in order_data.columns
            else "Unknown"
        )

        loyalty_tier = (
            order_data["loyalty_tier"].iloc[0]
            if "loyalty_tier" in order_data.columns
            else "Unknown"
        )

        # Order information

        order_date = order_data["order_date"].iloc[0]

        order_status = (
            order_data["order_status"].iloc[0]
            if "order_status" in order_data.columns
            else "Unknown"
        )

        store_id = (
            order_data["store_id"].iloc[0]
            if "store_id" in order_data.columns
            else "Unknown"
        )

        # Product information

        product_details = []

        for _, row in order_data.iterrows():
            product_name = row.get(
                "product_name",
                "Unknown product"
            )

            product_id = row.get(
                "product_id",
                "Unknown"
            )

            category = row.get(
                "category",
                "Unknown category"
            )

            quantity = row.get(
                "quantity",
                0
            )

            product_details.append(
                f"- {product_name} "
                f"(Product ID: {product_id}, "
                f"Category: {category}, "
                f"Quantity: {quantity})"
            )

        answer = (
            f"Order ID: {order_id}\n"
            f"Customer: {customer_name}\n"
            f"Home city: {customer_city}\n"
            f"Loyalty tier: {loyalty_tier}\n"
            f"Order date: {order_date}\n"
            f"Order status: {order_status}\n"
            f"Store ID: {store_id}\n\n"
            f"Products in this order:\n"
            + "\n".join(product_details)
        )

        return {
            "answer": answer,
            "sources": [
                "orders.csv",
                "customers.csv",
                "order_items.csv",
                "products.csv",
                "stores.csv",
            ],
        }

    # -----------------------------------------
    # Question 1: Revenue for a month and year
    # -----------------------------------------

    if (
        selected_month is not None
        and year_match
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
    ):
        selected_year = int(year_match.group(1))

        filtered_data = valid_dates[
            (
                valid_dates["order_date"].dt.year
                == selected_year
            )
            &
            (
                valid_dates["order_date"].dt.month
                == selected_month
            )
        ]

        total_revenue = filtered_data[
            "net_revenue_inr"
        ].sum()

        answer = (
            f"Net revenue for "
            f"{selected_month_name} {selected_year}: "
            f"₹{total_revenue:,.2f}"
        )

        return {
            "answer": answer,
            "sources": [
                "orders.csv",
                "order_items.csv",
            ],
        }

    # -----------------------------------------
    # Question 2: Monthly revenue breakdown
    # -----------------------------------------

    if any(
        phrase in question_lower
        for phrase in [
            "monthly revenue",
            "revenue by month",
            "monthly sales",
            "sales by month",
            "month-wise revenue",
        ]
    ):
        monthly_data = valid_dates.copy()

        if year_match:
            selected_year = int(
                year_match.group(1)
            )

            monthly_data = monthly_data[
                monthly_data["order_date"].dt.year
                == selected_year
            ]

        monthly_data["Month"] = (
            monthly_data["order_date"]
            .dt.to_period("M")
            .astype(str)
        )

        result = (
            monthly_data
            .groupby("Month")["net_revenue_inr"]
            .sum()
            .reset_index()
            .sort_values("Month")
        )

        result.columns = [
            "Month",
            "Total Revenue (INR)",
        ]

        answer = (
            "Monthly revenue breakdown:\n\n"
            + result.to_string(index=False)
        )

        return {
            "answer": answer,
            "sources": [
                "orders.csv",
                "order_items.csv",
            ],
        }

    # -----------------------------------------
    # Question 3: Revenue for a specific year
    # -----------------------------------------

    if (
        year_match
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
        and "store" not in question_lower
        and "category" not in question_lower
        and "product" not in question_lower
        and "city" not in question_lower
    ):
        selected_year = int(
            year_match.group(1)
        )

        filtered_data = valid_dates[
            valid_dates["order_date"].dt.year
            == selected_year
        ]

        total_revenue = filtered_data[
            "net_revenue_inr"
        ].sum()

        answer = (
            f"Net revenue for {selected_year}: "
            f"₹{total_revenue:,.2f}"
        )

        return {
            "answer": answer,
            "sources": [
                "orders.csv",
                "order_items.csv",
            ],
        }

    # -----------------------------------------
    # Question 4: Revenue by store
    # -----------------------------------------

    if "store" in question_lower and (
        "revenue" in question_lower
        or "sales" in question_lower
    ):
        store_data = dataset.copy()

        # Apply year filter when provided.

        if year_match:
            selected_year = int(
                year_match.group(1)
            )

            store_data = store_data[
                store_data["order_date"].dt.year
                == selected_year
            ]

        group_columns = []

        if "store_name" in store_data.columns:
            group_columns.append("store_name")

        if "city" in store_data.columns:
            group_columns.append("city")

        if not group_columns:
            group_columns = ["store_id"]

        result = (
            store_data
            .groupby(
                group_columns,
                dropna=False
            )["net_revenue_inr"]
            .sum()
            .reset_index()
            .sort_values(
                "net_revenue_inr",
                ascending=False
            )
            .head(5)
        )

        answer = (
            "Top stores by net revenue:\n\n"
            + result.to_string(index=False)
        )

        return {
            "answer": answer,
            "sources": [
                "orders.csv",
                "order_items.csv",
                "stores.csv",
            ],
        }

    # -----------------------------------------
    # Question 5: Revenue by product category
    # -----------------------------------------

    if "category" in question_lower and (
        "revenue" in question_lower
        or "sales" in question_lower
    ):
        category_data = dataset.copy()

        if year_match:
            selected_year = int(
                year_match.group(1)
            )

            category_data = category_data[
                category_data["order_date"].dt.year
                == selected_year
            ]

        result = (
            category_data
            .groupby(
                "category",
                dropna=False
            )["net_revenue_inr"]
            .sum()
            .reset_index()
            .sort_values(
                "net_revenue_inr",
                ascending=False
            )
        )

        result.columns = [
            "Category",
            "Total Revenue (INR)",
        ]

        answer = (
            "Revenue by product category:\n\n"
            + result.to_string(index=False)
        )

        return {
            "answer": answer,
            "sources": [
                "order_items.csv",
                "products.csv",
                "orders.csv",
            ],
        }

    # -----------------------------------------
    # Question 6: Top products by revenue
    # -----------------------------------------

    if "product" in question_lower and (
        "revenue" in question_lower
        or "sales" in question_lower
        or "best selling" in question_lower
    ):
        product_data = dataset.copy()

        if year_match:
            selected_year = int(
                year_match.group(1)
            )

            product_data = product_data[
                product_data["order_date"].dt.year
                == selected_year
            ]

        result = (
            product_data
            .groupby(
                ["product_name", "category"],
                dropna=False
            )["net_revenue_inr"]
            .sum()
            .reset_index()
            .sort_values(
                "net_revenue_inr",
                ascending=False
            )
            .head(5)
        )

        answer = (
            "Top products by net revenue:\n\n"
            + result.to_string(index=False)
        )

        return {
            "answer": answer,
            "sources": [
                "order_items.csv",
                "products.csv",
                "orders.csv",
            ],
        }

    # -----------------------------------------
    # Question 7: Customers with most orders
    # -----------------------------------------

    if "customer" in question_lower and any(
        phrase in question_lower
        for phrase in [
            "most orders",
            "highest orders",
            "top orders",
            "placed the most",
            "number of orders",
        ]
    ):
        result = (
            dataset
            .groupby(
                ["customer_id", "full_name"],
                dropna=False
            )["order_id"]
            .nunique()
            .reset_index(name="order_count")
            .sort_values(
                "order_count",
                ascending=False
            )
            .head(5)
        )

        answer = (
            "Customers with the most orders:\n\n"
            + result.to_string(index=False)
        )

        return {
            "answer": answer,
            "sources": [
                "customers.csv",
                "orders.csv",
            ],
        }

    # -----------------------------------------
    # Question 8: Returned order items
    # -----------------------------------------

    if "return" in question_lower:
        returned_items = dataset[
            dataset["is_returned"]
        ]["order_item_id"].nunique()

        answer = (
            f"Number of returned order items: "
            f"{returned_items}"
        )

        return {
            "answer": answer,
            "sources": [
                "order_items.csv",
                "returns.csv",
            ],
        }

    # -----------------------------------------
    # Question 9: Delivered order revenue
    # -----------------------------------------

    if "delivered" in question_lower and (
        "revenue" in question_lower
        or "sales" in question_lower
    ):
        delivered = dataset[
            dataset["order_status"]
            .astype(str)
            .str.lower()
            .str.strip()
            == "delivered"
        ]

        total_revenue = delivered[
            "net_revenue_inr"
        ].sum()

        answer = (
            "Net revenue from delivered orders: "
            f"₹{total_revenue:,.2f}"
        )

        return {
            "answer": answer,
            "sources": [
                "orders.csv",
                "order_items.csv",
            ],
        }

    # -----------------------------------------
    # Question 10: Revenue by city
    # -----------------------------------------

    if (
        "city" in question_lower
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
    ):
        result = (
            dataset
            .groupby(
                "city",
                dropna=False
            )["net_revenue_inr"]
            .sum()
            .reset_index()
            .sort_values(
                "net_revenue_inr",
                ascending=False
            )
        )

        result.columns = [
            "City",
            "Total Revenue (INR)",
        ]

        answer = (
            "Total revenue by city:\n\n"
            + result.to_string(index=False)
        )

        return {
            "answer": answer,
            "sources": [
                "orders.csv",
                "order_items.csv",
                "stores.csv",
            ],
        }

    # -----------------------------------------
    # Question 11: Average Order Value
    # -----------------------------------------

    if (
        "average order value" in question_lower
        or "average value of orders" in question_lower
        or "aov" in question_lower
    ):
        total_revenue = dataset[
            "net_revenue_inr"
        ].sum()

        total_orders = dataset[
            "order_id"
        ].nunique()

        if total_orders == 0:
            average_order_value = 0
        else:
            average_order_value = (
                total_revenue / total_orders
            )

        answer = (
            "Average Order Value (AOV): "
            f"₹{average_order_value:,.2f}"
        )

        return {
            "answer": answer,
            "sources": [
                "orders.csv",
                "order_items.csv",
            ],
        }

    # -----------------------------------------
    # Unsupported question
    # -----------------------------------------

    return {
        "answer": (
            "I could not identify a supported "
            "multi-CSV question. Try asking about "
            "store revenue, product category revenue, "
            "top products by revenue, customers with "
            "the most orders, returned items, "
            "delivered-order revenue, revenue by city, "
            "average order value, revenue by year, "
            "revenue by month, monthly revenue, "
            "or details of a specific order ID."
        ),
        "sources": [],
    }


# -----------------------------------------
# Multi-CSV question routing
# -----------------------------------------

def is_multi_csv_question(question):
    question_lower = question.lower()

    # 1. Specific order ID lookup

    if re.search(
        r"\bO\d{5}\b",
        question,
        re.IGNORECASE
    ):
        return True

    # 2. Store revenue or sales

    if "store" in question_lower and (
        "revenue" in question_lower
        or "sales" in question_lower
    ):
        return True

    # 3. Category revenue or sales

    if "category" in question_lower and (
        "revenue" in question_lower
        or "sales" in question_lower
    ):
        return True

    # 4. Product revenue or sales

    if "product" in question_lower and (
        "revenue" in question_lower
        or "sales" in question_lower
        or "best selling" in question_lower
    ):
        return True

    # 5. Customer order questions

    if "customer" in question_lower and any(
        phrase in question_lower
        for phrase in [
            "most orders",
            "highest orders",
            "top orders",
            "placed the most",
            "number of orders",
        ]
    ):
        return True

    # 6. Return questions

    if "return" in question_lower and any(
        phrase in question_lower
        for phrase in [
            "how many",
            "revenue",
            "refund",
            "count",
            "returned",
        ]
    ):
        return True

    # 7. Delivered order revenue

    if "delivered" in question_lower and (
        "revenue" in question_lower
        or "sales" in question_lower
    ):
        return True

    # 8. Revenue by city

    if "city" in question_lower and (
        "revenue" in question_lower
        or "sales" in question_lower
    ):
        return True

    # 9. Average Order Value

    if (
        "average order value" in question_lower
        or "average value of orders" in question_lower
        or "aov" in question_lower
    ):
        return True

    # 10. Date-based revenue questions

    if (
        "revenue" in question_lower
        or "sales" in question_lower
    ) and (
        "monthly" in question_lower
        or "month-wise" in question_lower
        or "by month" in question_lower
        or "month" in question_lower
        or any(
            month in question_lower
            for month in [
                "january",
                "february",
                "march",
                "april",
                "may",
                "june",
                "july",
                "august",
                "september",
                "october",
                "november",
                "december",
            ]
        )
        or any(
            str(year) in question_lower
            for year in range(2000, 2101)
        )
    ):
        return True

    return False
