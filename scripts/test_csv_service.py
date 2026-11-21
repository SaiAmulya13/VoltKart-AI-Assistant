
from backend.services.csv_service import (
    load_csv_tables,
    get_table_summary,
    validate_table_columns
)


print("\n========== CSV LOADING TEST ==========")

tables = load_csv_tables()

for name, df in tables.items():

    print(f"\nTable: {name}")

    print("Rows:", len(df))

    print("Columns:", df.columns.tolist())


print("\n========== DATASET SUMMARY ==========")

summary = get_table_summary()

for name, details in summary.items():

    print(f"\n{name}")

    print("Rows:", details["rows"])

    print("Number of columns:", details["columns_count"])


print("\n========== COLUMN VALIDATION ==========")

result = validate_table_columns({

    "orders": [
        "order_id",
        "customer_id",
        "store_id",
        "order_date",
        "order_status"
    ],

    "order_items": [
        "order_item_id",
        "order_id",
        "product_id",
        "quantity",
        "unit_price_inr",
        "discount_pct"
    ]

})

print(result)
