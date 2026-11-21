
import pandas as pd
from pathlib import Path

from backend.config import BASE_DIR
from backend.database.db import get_connection


# Required CSV tables in the VoltKart project
REQUIRED_TABLES = [
    "customers",
    "products",
    "stores",
    "orders",
    "order_items",
    "returns"
]


def load_csv_tables():

    """
    Load all required CSV tables.

    Priority:
    1. Latest uploaded CSV file
    2. Original sample CSV file

    Returns:
        Dictionary containing Pandas DataFrames.
    """

    tables = {}

    # ------------------------------------------------
    # STEP 1: Load original sample CSV files
    # ------------------------------------------------

    sample_dir = BASE_DIR / "data" / "tables"

    for table_name in REQUIRED_TABLES:

        file_path = sample_dir / f"{table_name}.csv"

        if file_path.exists():

            try:

                tables[table_name] = pd.read_csv(file_path)

                print(
                    f"Loaded sample dataset: {table_name}.csv"
                )

            except Exception as error:

                raise ValueError(
                    f"Unable to read sample file "
                    f"{table_name}.csv: {error}"
                )

    # ------------------------------------------------
    # STEP 2: Retrieve uploaded CSV file information
    # from SQLite database
    # ------------------------------------------------

    connection = get_connection()

    try:

        uploaded_files = connection.execute(
            """
            SELECT filename, stored_path, uploaded_at
            FROM uploaded_files
            WHERE file_type = '.csv'
            ORDER BY uploaded_at DESC
            """
        ).fetchall()

    finally:

        connection.close()

    # ------------------------------------------------
    # STEP 3: Replace sample files with latest uploads
    # ------------------------------------------------

    uploaded_names = set()

    for file in uploaded_files:

        # Get table name from uploaded filename
        original_name = Path(
            file["filename"]
        ).stem.lower()

        # Ignore files that are not required tables
        if original_name not in REQUIRED_TABLES:
            continue

        # Only use the latest upload for each table
        if original_name in uploaded_names:
            continue

        file_path = Path(file["stored_path"])

        if not file_path.exists():

            print(
                f"Uploaded file not found: {file_path}"
            )

            continue

        try:

            # Read uploaded CSV
            uploaded_df = pd.read_csv(file_path)

            # Replace original sample dataset
            tables[original_name] = uploaded_df

            uploaded_names.add(original_name)

            print(
                f"Loaded latest uploaded dataset: "
                f"{original_name}.csv"
            )

        except Exception as error:

            raise ValueError(
                f"Unable to read uploaded file "
                f"{file['filename']}: {error}"
            )

    # ------------------------------------------------
    # STEP 4: Check whether all required tables exist
    # ------------------------------------------------

    missing_tables = [
        table_name
        for table_name in REQUIRED_TABLES
        if table_name not in tables
    ]

    if missing_tables:

        raise FileNotFoundError(
            "Missing required CSV tables: "
            + ", ".join(missing_tables)
            + ". Please upload the missing datasets."
        )

    # ------------------------------------------------
    # STEP 5: Return all loaded DataFrames
    # ------------------------------------------------

    print("\nAll required CSV datasets loaded successfully!")

    return tables


def get_table_summary():

    """
    Get information about all loaded CSV datasets.

    Returns:
        Dictionary containing row counts and columns.
    """

    tables = load_csv_tables()

    summary = {}

    for table_name, df in tables.items():

        summary[table_name] = {

            "rows": len(df),

            "columns_count": len(df.columns),

            "columns": df.columns.tolist()

        }

    return summary


def get_single_table(table_name):

    """
    Retrieve one specific CSV DataFrame.
    """

    tables = load_csv_tables()

    if table_name not in tables:

        raise ValueError(
            f"Table '{table_name}' does not exist."
        )

    return tables[table_name]


def validate_table_columns(expected_columns):

    """
    Validate whether required columns exist
    in the loaded CSV datasets.

    expected_columns example:

    {
        "orders": [
            "order_id",
            "customer_id",
            "store_id",
            "order_date",
            "order_status"
        ]
    }
    """

    tables = load_csv_tables()

    errors = {}

    for table_name, required_columns in expected_columns.items():

        if table_name not in tables:

            errors[table_name] = "Table not found"

            continue

        actual_columns = set(
            tables[table_name].columns
        )

        missing_columns = [
            column
            for column in required_columns
            if column not in actual_columns
        ]

        if missing_columns:

            errors[table_name] = {
                "missing_columns": missing_columns
            }

    if errors:

        return {
            "valid": False,
            "errors": errors
        }

    return {
        "valid": True,
        "message": "All required columns are available."
    }
