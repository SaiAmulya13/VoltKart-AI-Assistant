
from backend.services.multi_csv_service import (
    load_multi_csv_tables,
    build_multi_csv_dataset,
)


# Load individual tables
tables = load_multi_csv_tables()

print("\nLoaded CSV tables:")

for name, df in tables.items():
    print(name, ":", df.shape)


# Build joined dataset
dataset = build_multi_csv_dataset()

print("\nJoined dataset shape:")
print(dataset.shape)

print("\nJoined dataset columns:")
print(list(dataset.columns))

print("\nFirst 5 joined rows:")
print(dataset.head())

print("\nRevenue columns:")
print(
    dataset[
        [
            "quantity",
            "unit_price_inr",
            "discount_pct",
            "gross_revenue_inr",
            "net_revenue_inr",
        ]
    ].head()
)

print("\nTotal net revenue:")
print(dataset["net_revenue_inr"].sum())

print("\nReturned order items:")
print(dataset["is_returned"].sum())
