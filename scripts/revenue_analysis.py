
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "tables"

# Step 1: Load datasets
orders = pd.read_csv(DATA_DIR / "orders.csv")
order_items = pd.read_csv(DATA_DIR / "order_items.csv")
stores = pd.read_csv(DATA_DIR / "stores.csv")

# Step 2: Convert order_date into datetime
orders["order_date"] = pd.to_datetime(
    orders["order_date"]
)

# Step 3: Join orders and order_items
sales = pd.merge(
    orders,
    order_items,
    on="order_id",
    how="inner"
)

# Step 4: Calculate line amount
sales["line_amount"] = (
    sales["quantity"]
    * sales["unit_price_inr"]
    * (1 - sales["discount_pct"] / 100)
)

# Step 5: Filter delivered orders from 2025
sales_2025 = sales[
    (sales["order_status"] == "Delivered") &
    (sales["order_date"].dt.year == 2025)
]

# Step 6: Join with stores
sales_2025 = pd.merge(
    sales_2025,
    stores,
    on="store_id",
    how="inner"
)

# Step 7: Calculate revenue for each store
store_revenue = sales_2025.groupby(
    ["store_id", "store_name", "store_manager"]
)["line_amount"].sum().reset_index()

# Step 8: Sort revenue from highest to lowest
store_revenue = store_revenue.sort_values(
    by="line_amount",
    ascending=False
)

# Step 9: Display results
print("\nSTORE REVENUE IN 2025")

print(
    store_revenue.to_string(index=False)
)

print("\nHIGHEST REVENUE STORE")

print(store_revenue.iloc[0])
