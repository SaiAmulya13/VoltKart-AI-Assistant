
from pathlib import Path
import re

import pandas as pd


# ==========================================
# Project paths
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TABLES_FOLDER = PROJECT_ROOT / "data" / "tables"


# ==========================================
# Expected CSV files
# ==========================================

TABLE_FILES = {
    "customers": "customers.csv",
    "orders": "orders.csv",
    "order_items": "order_items.csv",
    "products": "products.csv",
    "returns": "returns.csv",
    "stores": "stores.csv",
}


# ==========================================
# Load CSV tables
# ==========================================

def load_multi_csv_tables():
    """Load all six VoltKart CSV tables."""

    tables = {}

    for table_name, filename in TABLE_FILES.items():
        file_path = TABLES_FOLDER / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Required CSV file not found: {file_path}"
            )

        try:
            tables[table_name] = pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(
                f"Could not read {filename}: {e}"
            )

    return tables


# ==========================================
# Validate columns
# ==========================================

def check_required_columns(df, required_columns, table_name):
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


# ==========================================
# Build joined dataset
# ==========================================

def build_multi_csv_dataset():
    """
    Join customers, orders, order items, products,
    stores, and aggregated return information.
    """

    tables = load_multi_csv_tables()

    customers = tables["customers"].copy()
    orders = tables["orders"].copy()
    order_items = tables["order_items"].copy()
    products = tables["products"].copy()
    returns = tables["returns"].copy()
    stores = tables["stores"].copy()

    check_required_columns(
        customers,
        [
            "customer_id",
            "full_name",
            "home_city",
            "loyalty_tier",
        ],
        "customers",
    )

    check_required_columns(
        orders,
        [
            "order_id",
            "customer_id",
            "store_id",
            "order_date",
            "order_status",
        ],
        "orders",
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
        "order_items",
    )

    check_required_columns(
        products,
        [
            "product_id",
            "product_name",
            "category",
        ],
        "products",
    )

    check_required_columns(
        stores,
        [
            "store_id",
            "store_name",
            "city",
            "region",
            "store_manager",
        ],
        "stores",
    )

    check_required_columns(
        returns,
        [
            "return_id",
            "order_item_id",
            "return_reason",
            "refund_amount_inr",
        ],
        "returns",
    )

    # Join orders with customers.
    dataset = orders.merge(
        customers,
        on="customer_id",
        how="left",
    )

    # Join stores.
    dataset = dataset.merge(
        stores,
        on="store_id",
        how="left",
    )

    # Join order items.
    dataset = dataset.merge(
        order_items,
        on="order_id",
        how="left",
    )

    # Join products.
    dataset = dataset.merge(
        products,
        on="product_id",
        how="left",
    )

    # Aggregate returns before joining.
    # This prevents multiple return rows from
    # duplicating an order item's revenue.

    returns_summary = (
        returns.groupby(
            "order_item_id",
            as_index=False,
        )
        .agg(
            refund_amount_inr=(
                "refund_amount_inr",
                "sum",
            ),
            return_count=(
                "return_id",
                "nunique",
            ),
        )
    )

    dataset = dataset.merge(
        returns_summary,
        on="order_item_id",
        how="left",
    )

    # Convert numeric columns.
    numeric_columns = [
        "quantity",
        "unit_price_inr",
        "discount_pct",
        "refund_amount_inr",
        "return_count",
    ]

    for column in numeric_columns:
        dataset[column] = pd.to_numeric(
            dataset[column],
            errors="coerce",
        ).fillna(0)

    dataset["return_count"] = (
        dataset["return_count"].astype(int)
    )

    # Calculate revenue.
    dataset["gross_revenue_inr"] = (
        dataset["quantity"]
        * dataset["unit_price_inr"]
    )

    dataset["net_revenue_inr"] = (
        dataset["gross_revenue_inr"]
        * (1 - dataset["discount_pct"] / 100)
    )

    dataset["is_returned"] = (
        dataset["return_count"] > 0
    )

    dataset["order_date"] = pd.to_datetime(
        dataset["order_date"],
        errors="coerce",
    )

    return dataset


# ==========================================
# Helper functions
# ==========================================

def _response(answer, sources):
    return {
        "answer": answer,
        "sources": sources,
    }


def _table_answer(title, result, sources):
    return _response(
        title + "\n\n" + result.to_string(index=False),
        sources,
    )


def _year_from_question(question):
    match = re.search(
        r"\b(20\d{2})\b",
        question.lower(),
    )

    if match:
        return int(match.group(1))

    return None


def _filter_year(data, year):
    if year is None:
        return data

    return data[
        data["order_date"].dt.year == year
    ].copy()


def _filter_month(data, month):
    return data[
        data["order_date"].dt.month == month
    ].copy()


def _normal_text(series):
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
    )


# ==========================================
# Answer multi-CSV questions
# ==========================================

def answer_multi_csv_question(
    question,
    context_store=None,
):
    """
    Answer supported VoltKart multi-CSV questions.

    context_store:
        Optional store name from previous chat context.
        Pass this for follow-up questions such as
        'Which customer spent the most at that store?'
    """

    question_lower = question.lower().strip()

    dataset = build_multi_csv_dataset()

    valid_dates = dataset[
        dataset["order_date"].notna()
    ].copy()

    selected_year = _year_from_question(
        question_lower
    )

    sources = [
        "customers.csv",
        "orders.csv",
        "order_items.csv",
        "products.csv",
        "stores.csv",
        "returns.csv",
    ]

    # ==========================================
    # Order ID lookup
    # ==========================================

    order_match = re.search(
        r"\bO\d{5}\b",
        question,
        re.IGNORECASE,
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
            return _response(
                f"I could not find order {order_id}.",
                ["orders.csv"],
            )

        first = order_data.iloc[0]

        product_lines = []

        for _, row in order_data.iterrows():
            product_lines.append(
                f"- {row['product_name']} "
                f"(Product ID: {row['product_id']}, "
                f"Category: {row['category']}, "
                f"Quantity: {row['quantity']})"
            )

        answer = (
            f"Order ID: {order_id}\n"
            f"Customer: {first['full_name']}\n"
            f"Home city: {first['home_city']}\n"
            f"Loyalty tier: {first['loyalty_tier']}\n"
            f"Order date: {first['order_date']}\n"
            f"Order status: {first['order_status']}\n"
            f"Store: {first['store_name']}\n"
            f"Store manager: {first['store_manager']}\n\n"
            "Products in this order:\n"
            + "\n".join(product_lines)
        )

        return _response(answer, sources)

    # ==========================================
    # Q1: Store with highest revenue and manager
    # ==========================================

    if (
        "store" in question_lower
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
        and any(
            word in question_lower
            for word in [
                "highest",
                "most",
                "top",
                "manager",
                "which store",
            ]
        )
    ):
        store_data = _filter_year(
            valid_dates,
            selected_year,
        )

        result = (
            store_data.groupby(
                [
                    "store_id",
                    "store_name",
                    "city",
                    "region",
                    "store_manager",
                ],
                dropna=False,
            )["net_revenue_inr"]
            .sum()
            .reset_index()
            .sort_values(
                "net_revenue_inr",
                ascending=False,
            )
        )

        if result.empty:
            return _response(
                "No store revenue records were found.",
                ["orders.csv", "order_items.csv", "stores.csv"],
            )

        top_store = result.iloc[0]

        answer = (
            f"Highest-revenue store: "
            f"{top_store['store_name']}\n"
            f"Store ID: {top_store['store_id']}\n"
            f"City: {top_store['city']}\n"
            f"Region: {top_store['region']}\n"
            f"Store manager: {top_store['store_manager']}\n"
            f"Net revenue: "
            f"₹{top_store['net_revenue_inr']:,.2f}"
        )

        if selected_year:
            answer += f"\nYear: {selected_year}"

        answer += (
            "\n\nTop stores by net revenue:\n\n"
            + result.head(5).to_string(index=False)
        )

        return _response(
            answer,
            [
                "orders.csv",
                "order_items.csv",
                "stores.csv",
            ],
        )

    # ==========================================
    # Q2: Customer spending at a store
    # ==========================================

    if (
        "customer" in question_lower
        and (
            "spent" in question_lower
            or "spend" in question_lower
            or "spending" in question_lower
        )
        and (
            "store" in question_lower
            or "at that store" in question_lower
        )
    ):
        store_name = context_store

        # Try to extract a store name from the question.
        store_match = re.search(
            r"\bat\s+([a-zA-Z0-9\s&'-]+?)(?:\?|$)",
            question,
            re.IGNORECASE,
        )

        if store_match:
            possible_store = store_match.group(1).strip()

            if possible_store.lower() not in [
                "that store",
                "the store",
                "same store",
            ]:
                store_name = possible_store

        if not store_name:
            return _response(
                "I need the store name from the previous "
                "question to calculate customer spending "
                "at that store. Please mention the store "
                "name or pass it as context_store.",
                ["orders.csv", "order_items.csv", "stores.csv"],
            )

        store_mask = (
            _normal_text(dataset["store_name"])
            .str.contains(
                re.escape(str(store_name).lower()),
                na=False,
            )
        )

        store_data = dataset[store_mask].copy()

        if store_data.empty:
            return _response(
                f"No store matching '{store_name}' "
                "was found.",
                ["stores.csv"],
            )

        store_data = _filter_year(
            store_data,
            selected_year,
        )

        result = (
            store_data.groupby(
                ["customer_id", "full_name"],
                dropna=False,
            )["net_revenue_inr"]
            .sum()
            .reset_index(name="customer_spend_inr")
            .sort_values(
                "customer_spend_inr",
                ascending=False,
            )
        )

        if result.empty:
            return _response(
                f"No customer spending data was found "
                f"for {store_name}.",
                sources,
            )

        top_customer = result.iloc[0]

        answer = (
            f"Store: {store_name}\n"
            f"Highest-spending customer: "
            f"{top_customer['full_name']}\n"
            f"Customer ID: {top_customer['customer_id']}\n"
            f"Total spend: "
            f"₹{top_customer['customer_spend_inr']:,.2f}"
        )

        return _response(
            answer,
            [
                "customers.csv",
                "orders.csv",
                "order_items.csv",
                "stores.csv",
            ],
        )

    # ==========================================
    # Q4: Platinum Bengaluru laptop customers
    # Q1 2026
    # ==========================================

    if (
        "platinum" in question_lower
        and "bengaluru" in question_lower
        and "laptop" in question_lower
    ):
        filtered = dataset.copy()

        filtered = filtered[
            _normal_text(filtered["loyalty_tier"])
            == "platinum"
        ]

        filtered = filtered[
            _normal_text(filtered["home_city"])
            == "bengaluru"
        ]

        product_mask = (
            _normal_text(filtered["product_name"])
            .str.contains("laptop", na=False)
            |
            _normal_text(filtered["category"])
            .str.contains("laptop", na=False)
        )

        filtered = filtered[product_mask]

        # Q1 means January through March.
        if "q1" in question_lower or "first quarter" in question_lower:
            filtered = filtered[
                (filtered["order_date"].dt.year == 2026)
                & (filtered["order_date"].dt.month.isin([1, 2, 3]))
            ]
        elif selected_year:
            filtered = filtered[
                filtered["order_date"].dt.year == selected_year
            ]

        if filtered.empty:
            return _response(
                "No matching Platinum customers from "
                "Bengaluru who purchased laptops were "
                "found for the selected period.",
                [
                    "customers.csv",
                    "orders.csv",
                    "order_items.csv",
                    "products.csv",
                ],
            )

        result = (
            filtered.groupby(
                [
                    "customer_id",
                    "full_name",
                    "home_city",
                    "loyalty_tier",
                ],
                dropna=False,
            )
            .agg(
                order_count=("order_id", "nunique"),
                laptop_units=("quantity", "sum"),
                spend_inr=("net_revenue_inr", "sum"),
            )
            .reset_index()
            .sort_values(
                "spend_inr",
                ascending=False,
            )
        )

        return _table_answer(
            "Platinum customers from Bengaluru "
            "who purchased laptops:",
            result,
            [
                "customers.csv",
                "orders.csv",
                "order_items.csv",
                "products.csv",
            ],
        )

    # ==========================================
    # Q5: Refund amount by store region
    # ==========================================

    if (
        "refund" in question_lower
        and (
            "region" in question_lower
            or "regional" in question_lower
        )
    ):
        returns = load_multi_csv_tables()["returns"].copy()
        order_items = load_multi_csv_tables()["order_items"].copy()
        orders = load_multi_csv_tables()["orders"].copy()
        stores = load_multi_csv_tables()["stores"].copy()

        returns["refund_amount_inr"] = pd.to_numeric(
            returns["refund_amount_inr"],
            errors="coerce",
        ).fillna(0)

        refund_data = returns.merge(
            order_items[
                ["order_item_id", "order_id"]
            ],
            on="order_item_id",
            how="left",
        )

        refund_data = refund_data.merge(
            orders[
                ["order_id", "store_id", "order_date"]
            ],
            on="order_id",
            how="left",
        )

        refund_data = refund_data.merge(
            stores[
                ["store_id", "region"]
            ],
            on="store_id",
            how="left",
        )

        refund_data["order_date"] = pd.to_datetime(
            refund_data["order_date"],
            errors="coerce",
        )

        if selected_year:
            refund_data = refund_data[
                refund_data["order_date"].dt.year
                == selected_year
            ]

        result = (
            refund_data.groupby(
                "region",
                dropna=False,
            )["refund_amount_inr"]
            .sum()
            .reset_index(name="total_refund_inr")
            .sort_values(
                "total_refund_inr",
                ascending=False,
            )
        )

        return _table_answer(
            "Total refund amount by store region:",
            result,
            [
                "returns.csv",
                "order_items.csv",
                "orders.csv",
                "stores.csv",
            ],
        )

    # ==========================================
    # Q3: Most returned product and common reason
    # ==========================================

    if (
        "return" in question_lower
        and (
            "product" in question_lower
            or "reason" in question_lower
            or "most" in question_lower
        )
    ):
        tables = load_multi_csv_tables()

        returns = tables["returns"].copy()
        order_items = tables["order_items"].copy()
        products = tables["products"].copy()

        return_data = returns.merge(
            order_items[
                [
                    "order_item_id",
                    "product_id",
                    "quantity",
                ]
            ],
            on="order_item_id",
            how="left",
        )

        return_data = return_data.merge(
            products[
                [
                    "product_id",
                    "product_name",
                    "category",
                ]
            ],
            on="product_id",
            how="left",
        )

        # Count distinct return records per product.
        product_returns = (
            return_data.groupby(
                [
                    "product_id",
                    "product_name",
                    "category",
                ],
                dropna=False,
            )["return_id"]
            .nunique()
            .reset_index(name="return_count")
            .sort_values(
                "return_count",
                ascending=False,
            )
        )

        if product_returns.empty:
            return _response(
                "No return records were found.",
                ["returns.csv", "order_items.csv", "products.csv"],
            )

        most_returned = product_returns.iloc[0]

        product_id = most_returned["product_id"]

        product_data = return_data[
            return_data["product_id"] == product_id
        ]

        common_reason = (
            product_data["return_reason"]
            .dropna()
            .astype(str)
            .value_counts()
        )

        if common_reason.empty:
            reason_text = "No return reason available"
        else:
            reason_text = common_reason.index[0]

        answer = (
            f"Most returned product: "
            f"{most_returned['product_name']}\n"
            f"Category: {most_returned['category']}\n"
            f"Number of return records: "
            f"{most_returned['return_count']}\n"
            f"Most common reason for this product: "
            f"{reason_text}\n\n"
            "Top returned products:\n\n"
            + product_returns.head(5).to_string(index=False)
        )

        return _response(
            answer,
            [
                "returns.csv",
                "order_items.csv",
                "products.csv",
            ],
        )

    # ==========================================
    # Q16: Monthly smartphone units sold in 2025
    # ==========================================

    if (
        "smartphone" in question_lower
        and (
            "month" in question_lower
            or "monthly" in question_lower
            or "units sold" in question_lower
        )
    ):
        smartphone_data = dataset.copy()

        product_mask = (
            _normal_text(smartphone_data["product_name"])
            .str.contains("smartphone", na=False)
            |
            _normal_text(smartphone_data["category"])
            .str.contains("smartphone", na=False)
        )

        smartphone_data = smartphone_data[
            product_mask
        ]

        year = selected_year or 2025

        smartphone_data = smartphone_data[
            smartphone_data["order_date"].dt.year == year
        ]

        smartphone_data["month"] = (
            smartphone_data["order_date"].dt.month
        )

        result = (
            smartphone_data.groupby("month")["quantity"]
            .sum()
            .reset_index(name="units_sold")
            .sort_values("month")
        )

        month_labels = {
            1: "January",
            2: "February",
            3: "March",
            4: "April",
            5: "May",
            6: "June",
            7: "July",
            8: "August",
            9: "September",
            10: "October",
            11: "November",
            12: "December",
        }

        result["month"] = result["month"].map(
            month_labels
        )

        return _table_answer(
            f"Monthly smartphone units sold in {year}:",
            result,
            [
                "orders.csv",
                "order_items.csv",
                "products.csv",
            ],
        )

    # ==========================================
    # Revenue for a specific month and year
    # ==========================================

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

    for name, number in month_names.items():
        if re.search(
            rf"\b{name}\b",
            question_lower,
        ):
            selected_month = number
            selected_month_name = name.capitalize()
            break

    if (
        selected_month
        and selected_year
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
    ):
        filtered = valid_dates[
            (valid_dates["order_date"].dt.year == selected_year)
            & (valid_dates["order_date"].dt.month == selected_month)
        ]

        total = filtered["net_revenue_inr"].sum()

        return _response(
            f"Net revenue for {selected_month_name} "
            f"{selected_year}: ₹{total:,.2f}",
            ["orders.csv", "order_items.csv"],
        )

    # ==========================================
    # Monthly revenue
    # ==========================================

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
        monthly_data = _filter_year(
            valid_dates,
            selected_year,
        )

        monthly_data["Month"] = (
            monthly_data["order_date"]
            .dt.to_period("M")
            .astype(str)
        )

        result = (
            monthly_data.groupby("Month")["net_revenue_inr"]
            .sum()
            .reset_index()
            .sort_values("Month")
        )

        result.columns = [
            "Month",
            "Total Revenue (INR)",
        ]

        return _table_answer(
            "Monthly revenue breakdown:",
            result,
            ["orders.csv", "order_items.csv"],
        )

    # ==========================================
    # Revenue for a year
    # ==========================================

    if (
        selected_year
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
        and not any(
            word in question_lower
            for word in [
                "store",
                "category",
                "product",
                "city",
            ]
        )
    ):
        filtered = _filter_year(
            valid_dates,
            selected_year,
        )

        total = filtered["net_revenue_inr"].sum()

        return _response(
            f"Net revenue for {selected_year}: "
            f"₹{total:,.2f}",
            ["orders.csv", "order_items.csv"],
        )

    # ==========================================
    # Revenue by store
    # ==========================================

    if (
        "store" in question_lower
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
    ):
        store_data = _filter_year(
            valid_dates,
            selected_year,
        )

        result = (
            store_data.groupby(
                [
                    "store_name",
                    "city",
                    "region",
                ],
                dropna=False,
            )["net_revenue_inr"]
            .sum()
            .reset_index()
            .sort_values(
                "net_revenue_inr",
                ascending=False,
            )
            .head(5)
        )

        return _table_answer(
            "Top stores by net revenue:",
            result,
            ["orders.csv", "order_items.csv", "stores.csv"],
        )

    # ==========================================
    # Revenue by product category
    # ==========================================

    if (
        "category" in question_lower
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
    ):
        category_data = _filter_year(
            valid_dates,
            selected_year,
        )

        result = (
            category_data.groupby(
                "category",
                dropna=False,
            )["net_revenue_inr"]
            .sum()
            .reset_index()
            .sort_values(
                "net_revenue_inr",
                ascending=False,
            )
        )

        result.columns = [
            "Category",
            "Total Revenue (INR)",
        ]

        return _table_answer(
            "Revenue by product category:",
            result,
            ["order_items.csv", "products.csv", "orders.csv"],
        )

    # ==========================================
    # Top products by revenue
    # ==========================================

    if (
        "product" in question_lower
        and (
            "revenue" in question_lower
            or "sales" in question_lower
            or "best selling" in question_lower
        )
    ):
        product_data = _filter_year(
            valid_dates,
            selected_year,
        )

        result = (
            product_data.groupby(
                ["product_name", "category"],
                dropna=False,
            )["net_revenue_inr"]
            .sum()
            .reset_index()
            .sort_values(
                "net_revenue_inr",
                ascending=False,
            )
            .head(5)
        )

        return _table_answer(
            "Top products by net revenue:",
            result,
            ["order_items.csv", "products.csv", "orders.csv"],
        )

    # ==========================================
    # Customers with most orders
    # ==========================================

    if (
        "customer" in question_lower
        and any(
            phrase in question_lower
            for phrase in [
                "most orders",
                "highest orders",
                "top orders",
                "placed the most",
                "number of orders",
            ]
        )
    ):
        result = (
            dataset.groupby(
                ["customer_id", "full_name"],
                dropna=False,
            )["order_id"]
            .nunique()
            .reset_index(name="order_count")
            .sort_values(
                "order_count",
                ascending=False,
            )
            .head(5)
        )

        return _table_answer(
            "Customers with the most orders:",
            result,
            ["customers.csv", "orders.csv"],
        )

    # ==========================================
    # Count returned order items
    # Keep this after specialized return queries
    # ==========================================

    if (
        "return" in question_lower
        and any(
            phrase in question_lower
            for phrase in [
                "how many",
                "count",
                "number of",
                "returned items",
                "order items",
            ]
        )
    ):
        returned_items = dataset[
            dataset["is_returned"]
        ]["order_item_id"].nunique()

        return _response(
            f"Number of returned order items: "
            f"{returned_items}",
            ["order_items.csv", "returns.csv"],
        )

    # ==========================================
    # Delivered order revenue
    # ==========================================

    if (
        "delivered" in question_lower
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
    ):
        delivered = dataset[
            _normal_text(dataset["order_status"])
            == "delivered"
        ]

        total = delivered["net_revenue_inr"].sum()

        return _response(
            f"Net revenue from delivered orders: "
            f"₹{total:,.2f}",
            ["orders.csv", "order_items.csv"],
        )

    # ==========================================
    # Revenue by city
    # ==========================================

    if (
        "city" in question_lower
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
    ):
        result = (
            dataset.groupby(
                "city",
                dropna=False,
            )["net_revenue_inr"]
            .sum()
            .reset_index()
            .sort_values(
                "net_revenue_inr",
                ascending=False,
            )
        )

        result.columns = [
            "City",
            "Total Revenue (INR)",
        ]

        return _table_answer(
            "Total revenue by store city:",
            result,
            ["orders.csv", "order_items.csv", "stores.csv"],
        )

    # ==========================================
    # Average Order Value
    # ==========================================

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
            aov = 0
        else:
            aov = total_revenue / total_orders

        return _response(
            f"Average Order Value (AOV): ₹{aov:,.2f}",
            ["orders.csv", "order_items.csv"],
        )

    # ==========================================
    # Unsupported question
    # ==========================================

    return _response(
        "I could not identify a supported multi-CSV "
        "question. Try asking about store revenue, "
        "customer spending at a store, returned products, "
        "refunds by region, monthly smartphone units, "
        "product category revenue, top products, "
        "customers with the most orders, delivered revenue, "
        "revenue by city, average order value, or a "
        "specific order ID.",
        [],
    )


# ==========================================
# Multi-CSV question routing
# ==========================================

def is_multi_csv_question(question):
    question_lower = question.lower()

    # Specific order ID.
    if re.search(
        r"\bO\d{5}\b",
        question,
        re.IGNORECASE,
    ):
        return True

    # Assessment-specific questions.
    assessment_keywords = [
        "highest revenue store",
        "store with the highest revenue",
        "store generated the most revenue",
        "customer spent the most at",
        "spending at that store",
        "at the same store",
        "most returned product",
        "returned most often",
        "common return reason",
        "platinum customers",
        "platinum customer",
        "bengaluru",
        "laptop",
        "refund amount by region",
        "refunds by region",
        "store region",
        "smartphone units sold",
        "monthly smartphone",
        "units sold per month",
    ]

    if any(
        keyword in question_lower
        for keyword in assessment_keywords
    ):
        return True

    # Store revenue.
    if (
        "store" in question_lower
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
    ):
        return True

    # Category revenue.
    if (
        "category" in question_lower
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
    ):
        return True

    # Product revenue.
    if (
        "product" in question_lower
        and (
            "revenue" in question_lower
            or "sales" in question_lower
            or "best selling" in question_lower
        )
    ):
        return True

    # Customer order questions.
    if (
        "customer" in question_lower
        and any(
            phrase in question_lower
            for phrase in [
                "most orders",
                "highest orders",
                "top orders",
                "placed the most",
                "number of orders",
            ]
        )
    ):
        return True

    # Return analytics.
    if (
        "return" in question_lower
        and any(
            phrase in question_lower
            for phrase in [
                "how many",
                "count",
                "number of",
                "returned",
                "product",
                "reason",
                "most",
            ]
        )
    ):
        return True

    # Refund analytics.
    if (
        "refund" in question_lower
        and "region" in question_lower
    ):
        return True

    # Delivered revenue.
    if (
        "delivered" in question_lower
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
    ):
        return True

    # City revenue.
    if (
        "city" in question_lower
        and (
            "revenue" in question_lower
            or "sales" in question_lower
        )
    ):
        return True

    # AOV.
    if (
        "average order value" in question_lower
        or "average value of orders" in question_lower
        or "aov" in question_lower
    ):
        return True

    # Date-based revenue.
    if (
        "revenue" in question_lower
        or "sales" in question_lower
    ) and (
        "monthly" in question_lower
        or "month-wise" in question_lower
        or "by month" in question_lower
        or "month" in question_lower
        or re.search(r"\b20\d{2}\b", question_lower)
    ):
        return True

    return False
