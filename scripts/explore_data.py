
import pandas as pd
from pathlib import Path

# Step 1: Locate the project folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Step 2: Locate the CSV folder
DATA_DIR = BASE_DIR / "data" / "tables"

# Step 3: Read all six CSV files
customers = pd.read_csv(DATA_DIR / "customers.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
stores = pd.read_csv(DATA_DIR / "stores.csv")
orders = pd.read_csv(DATA_DIR / "orders.csv")
order_items = pd.read_csv(DATA_DIR / "order_items.csv")
returns = pd.read_csv(DATA_DIR / "returns.csv")

# Step 4: Store all DataFrames in one dictionary
tables = {
    "customers": customers,
    "products": products,
    "stores": stores,
    "orders": orders,
    "order_items": order_items,
    "returns": returns
}

# Step 5: Display dataset information
for name, df in tables.items():

    print("\n-----------------------------")
    print("TABLE:", name)
    print("-----------------------------")

    print("Rows and Columns:", df.shape)

    print("\nColumn Names:")
    print(df.columns.tolist())

    print("\nFirst Five Records:")
    print(df.head())

    print("\nMissing Values:")
    print(df.isnull().sum())

    print("\nDuplicate Rows:")
    print(df.duplicated().sum())
