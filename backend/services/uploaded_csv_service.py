
import re
from pathlib import Path

import pandas as pd

from backend.config import BASE_DIR
from backend.database.db import get_connection


# ============================================================
# 1. LOAD UPLOADED CSV
# ============================================================

def load_latest_uploaded_csv(requested_filename=None):
    """
    Load a requested CSV file, or the latest uploaded CSV.

    Returns:
        filename, DataFrame
    """
    connection = get_connection()

    try:
        if requested_filename:
            uploaded_file = connection.execute(
                """
                SELECT filename, stored_path
                FROM uploaded_files
                WHERE LOWER(file_type) = '.csv'
                  AND LOWER(filename) = LOWER(?)
                ORDER BY uploaded_at DESC
                LIMIT 1
                """,
                (requested_filename,)
            ).fetchone()
        else:
            uploaded_file = connection.execute(
                """
                SELECT filename, stored_path
                FROM uploaded_files
                WHERE LOWER(file_type) = '.csv'
                ORDER BY uploaded_at DESC
                LIMIT 1
                """
            ).fetchone()
    finally:
        connection.close()

    if not uploaded_file:
        if requested_filename:
            raise FileNotFoundError(
                f"CSV file '{requested_filename}' was not found. "
                "Check the filename or upload it first."
            )

        raise FileNotFoundError(
            "No uploaded CSV file was found. Please upload a CSV first."
        )

    filename = uploaded_file["filename"]
    stored_path = uploaded_file["stored_path"]

    file_path = Path(stored_path)

    if not file_path.is_absolute():
        file_path = BASE_DIR / file_path

    if not file_path.exists():
        raise FileNotFoundError(
            f"The uploaded CSV file could not be found: {filename}"
        )

    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig")
    except Exception as error:
        raise ValueError(
            f"Unable to read uploaded CSV: {error}"
        ) from error

    if df.empty:
        raise ValueError("The uploaded CSV contains no data rows.")

    # Clean spaces accidentally added to column headers.
    df.columns = [str(column).strip() for column in df.columns]

    return filename, df


def get_requested_csv_filename(question):
    """Detect a CSV filename mentioned in the question."""
    match = re.search(
        r"([a-zA-Z0-9_. -]+\.csv)\b",
        str(question),
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return None


# ============================================================
# 2. TEXT NORMALIZATION
# ============================================================

def normalize_text(text):
    """Convert text into lowercase words."""
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


# ============================================================
# 3. COLUMN UTILITIES
# ============================================================

def is_id_column(column):
    """Identify columns that contain IDs."""
    name = normalize_text(column)

    return (
        name == "id"
        or name.endswith(" id")
        or name.endswith(" identifier")
        or name.endswith(" number")
    )


def get_numeric_columns(df):
    """Return numeric columns, excluding identifier columns."""
    numeric_columns = []

    for column in df.columns:
        if is_id_column(column):
            continue

        values = pd.to_numeric(df[column], errors="coerce")

        if values.notna().any():
            numeric_columns.append(column)

    return numeric_columns


def get_date_columns(df):
    """Return columns that contain date-like values."""
    date_columns = []

    for column in df.columns:
        column_name = normalize_text(column)

        if not any(
            word in column_name
            for word in ["date", "time", "year", "month"]
        ):
            continue

        values = pd.to_datetime(df[column], errors="coerce")

        if values.notna().any():
            date_columns.append(column)

    return date_columns



def find_matching_column(question, df, numeric_only=False):
    """
    Find the most relevant column for a question.

    Priority:
    1. Exact column name
    2. Semantic matching
    3. Token matching
    """

    q = normalize_text(question)
    question_tokens = set(q.split())

    # Step 1: Match exact column names first
    for column in df.columns:

        column_name = normalize_text(str(column))

        if column_name in q:

            if numeric_only:
                if pd.api.types.is_numeric_dtype(df[column]):
                    return column
            else:
                return column

    # Step 2: Get candidate columns
    if numeric_only:
        candidates = get_numeric_columns(df)
    else:
        candidates = list(df.columns)

    if not candidates:
        return None

    # Step 3: Semantic matching
    semantic_rules = {
        "city": ["city", "location", "place"],
        "customer": ["customer", "client", "buyer"],
        "name": ["name", "customer name", "full name"],
        "date": ["date", "time"],
        "price": ["price", "cost", "amount"],
        "quantity": ["quantity", "qty", "count"],
        "tier": ["tier", "loyalty", "membership"],
        "age": ["age", "years old"],
    }

    for keyword, related_terms in semantic_rules.items():

        if keyword in q or any(term in q for term in related_terms):

            for column in candidates:

                column_name = normalize_text(str(column))

                if any(term in column_name for term in related_terms):
                    return column

    # Step 4: Token matching
    best_column = None
    best_score = 0

    for column in candidates:

        column_name = normalize_text(str(column))
        column_tokens = set(column_name.split())

        common_tokens = question_tokens.intersection(column_tokens)
        score = len(common_tokens)

        if score > best_score:
            best_score = score
            best_column = column

    if best_score > 0:
        return best_column

    return None

    # --------------------------------------------------------
    # 2. Semantic matching
    # --------------------------------------------------------

    semantic_rules = [
        (
            ["location", "city", "town", "where", "home"],
            ["home city", "city", "location", "town", "address"]
        ),
        (
            ["loyalty", "tier", "membership"],
            ["loyalty tier", "tier", "membership tier", "member type"]
        ),
        (
            ["signup", "sign up", "registration", "registered", "joined"],
            ["signup date", "registration date", "joined date", "date joined"]
        ),
        (
            ["customer name", "person", "name"],
            ["full name", "customer name", "name"]
        ),
        (
            ["quantity", "qty", "units"],
            ["quantity", "qty", "units", "order quantity"]
        ),
        (
            ["price", "cost", "unit price"],
            ["unit price", "price", "cost", "amount"]
        ),
        (
            ["age", "years old"],
            ["age", "customer age"]
        ),
        (
            ["discount"],
            ["discount", "discount pct", "discount percent"]
        ),
        (
            ["salary", "wage", "pay"],
            ["salary", "wage", "pay", "compensation"]
        ),
        (
            ["revenue", "sales", "income"],
            ["revenue", "sales", "sale amount", "sales amount", "income"]
        ),
        (
            ["profit", "earnings"],
            ["profit", "earnings", "net income"]
        ),
        (
            ["rating", "score", "marks", "grade"],
            ["rating", "score", "marks", "grade"]
        ),
    ]

    for question_terms, header_terms in semantic_rules:
        if not any(term in q for term in question_terms):
            continue

        for header_term in header_terms:
            for column in candidates:
                column_name = normalize_text(column)

                if (
                    column_name == header_term
                    or header_term in column_name
                ):
                    return column

    # --------------------------------------------------------
    # 3. Token scoring
    # --------------------------------------------------------

    best_column = None
    best_score = 0

    for column in candidates:
        column_name = normalize_text(column)
        column_tokens = set(column_name.split())

        score = len(question_tokens.intersection(column_tokens))

        if column_name and column_name in q:
            score += 10

        # Avoid choosing customer_id when the user asks
        # about customers generally.
        if is_id_column(column):
            if not any(
                word in question_tokens
                for word in ["id", "identifier", "number", "code"]
            ):
                score -= 5

        if score > best_score:
            best_score = score
            best_column = column

    if best_score > 0:
        return best_column

    if numeric_only and len(candidates) == 1:
        return candidates[0]

    return None


# ============================================================
# 4. FORMATTING
# ============================================================

def format_number(value):
    """Format a number without assuming currency."""
    try:
        value = float(value)

        if pd.isna(value):
            return "N/A"

        if value.is_integer():
            return f"{int(value):,}"

        return f"{value:,.2f}"

    except (TypeError, ValueError):
        return str(value)


def format_table(dataframe, max_rows=20):
    """Format a DataFrame as readable text."""
    if dataframe.empty:
        return "No records found."

    return dataframe.head(max_rows).to_string(index=False)


def available_columns_message(df):
    return ", ".join(str(column) for column in df.columns)


# ============================================================
# 5. CITATIONS
# ============================================================

def build_uploaded_csv_citation(
    filename,
    computation,
    result_context=None
):
    citation = {
        "type": "uploaded_csv",
        "filename": filename,
        "computation": computation
    }

    if result_context:
        citation["result_context"] = result_context

    return [citation]


def make_result(
    filename,
    answer,
    computation,
    result_context=None
):
    return {
        "answer": answer,
        "citations": build_uploaded_csv_citation(
            filename,
            computation,
            result_context
        )
    }


# ============================================================
# 6. ANSWER CSV QUESTIONS
# ============================================================

def answer_uploaded_csv_question(question):

    requested_filename = get_requested_csv_filename(question)

    filename, df = load_latest_uploaded_csv(
        requested_filename
    )

    q = normalize_text(question)

    # ========================================================
    # 1. ROW COUNT
    # ========================================================

    row_count_phrases = [
        "how many rows",
        "number of rows",
        "row count",
        "how many records",
        "number of records",
        "how many entries",
        "record count",
        "how many customers",
        "how many products",
        "how many orders"
    ]

    if (
        any(phrase in q for phrase in row_count_phrases)
        and not any(word in q for word in ["each", "per", "grouped"])
    ):
        return make_result(
            filename,
            f"{filename} contains {len(df):,} data rows.",
            "Counted the data rows.",
            {"rows": int(len(df))}
        )

    # ========================================================
    # 2. COLUMN NAMES
    # ========================================================

    if (
        "column" in q
        and any(
            word in q
            for word in ["name", "list", "show", "available", "what are"]
        )
    ):
        return make_result(
            filename,
            f"Columns in {filename}: {available_columns_message(df)}",
            "Retrieved the column names.",
            {"columns": df.columns.tolist()}
        )

    # ========================================================
    # 3. MISSING VALUES
    # ========================================================

    if any(
        phrase in q
        for phrase in [
            "missing values",
            "null values",
            "empty values",
            "missing data",
            "null data"
        ]
    ):
        missing = df.isnull().sum()
        missing_columns = missing[missing > 0]
        total_missing = int(missing.sum())

        if missing_columns.empty:
            answer = f"No missing values were found in {filename}."
        else:
            details = [
                f"{column}: {int(count)}"
                for column, count in missing_columns.items()
            ]

            answer = (
                f"Total missing values: {total_missing}\n\n"
                + "\n".join(details)
            )

        return make_result(
            filename,
            answer,
            "Counted missing values using pandas.",
            {
                "total_missing": total_missing,
                "missing_by_column": {
                    str(column): int(count)
                    for column, count in missing.items()
                }
            }
        )

    # ========================================================
    # 4. DUPLICATE ROWS
    # ========================================================

    if any(
        phrase in q
        for phrase in [
            "duplicate rows",
            "duplicate records",
            "duplicated rows",
            "duplicate data"
        ]
    ):
        duplicate_count = int(df.duplicated().sum())

        return make_result(
            filename,
            f"{filename} contains {duplicate_count:,} duplicate rows.",
            "Counted duplicate rows.",
            {"duplicate_rows": duplicate_count}
        )

    # ========================================================
    # 5. DATASET SUMMARY
    # ========================================================

    if any(
        phrase in q
        for phrase in [
            "describe dataset",
            "statistical summary",
            "data summary",
            "dataset summary",
            "summary statistics",
            "describe the data"
        ]
    ):
        numeric_columns = get_numeric_columns(df)

        if not numeric_columns:
            return make_result(
                filename,
                "No numeric columns were found for statistical summary.",
                "Inspected numeric columns."
            )

        summary = df[numeric_columns].describe()

        return make_result(
            filename,
            f"Statistical summary of {filename}:\n\n"
            + summary.round(2).to_string(),
            "Calculated descriptive statistics.",
            {"numeric_columns": numeric_columns}
        )

    # ========================================================
    # 6. GROUP BY / COUNT BY CATEGORY
    # ========================================================

    asks_group_count = (
        any(word in q for word in ["how many", "count", "number of"])
        and any(word in q for word in ["each", "every", "per", "by"])
    )

    asks_group_analysis = any(
        phrase in q
        for phrase in [
            "group by",
            "compare",
            "by category",
            "by region",
            "by department",
            "by product",
            "by gender",
            "by store",
            "by loyalty tier",
            "by location"
        ]
    )

    if asks_group_count or asks_group_analysis:

        group_column = find_matching_column(
            question,
            df,
            numeric_only=False
        )

        # If "by <column>" is present, use that column.
        group_match = re.search(
            r"\bby\s+([a-z0-9_ ]+)",
            q
        )

        if group_match:
            group_phrase = group_match.group(1).strip()

            group_phrase = re.split(
                r"\b(?:and|with|having|where|for|show|calculate)\b",
                group_phrase
            )[0].strip()

            phrase_column = find_matching_column(
                group_phrase,
                df,
                numeric_only=False
            )

            if phrase_column is not None:
                group_column = phrase_column

        if group_column is None:
            return {
                "answer": (
                    "Please mention the column to group by. "
                    f"Available columns: {available_columns_message(df)}"
                ),
                "citations": []
            }

        # Questions such as:
        # "How many customers are in each loyalty_tier?"
        if asks_group_count:
            grouped = (
                df.groupby(group_column, dropna=False)
                .size()
                .reset_index(name="record_count")
                .sort_values("record_count", ascending=False)
            )

            return make_result(
                filename,
                f"Record count grouped by '{group_column}':\n\n"
                + format_table(grouped),
                f"Counted records grouped by '{group_column}'.",
                {
                    "group_column": str(group_column),
                    "counts": grouped.to_dict(orient="records")
                }
            )

        metric_column = find_matching_column(
            question,
            df,
            numeric_only=True
        )

        if metric_column and metric_column != group_column:
            grouped = df.groupby(
                group_column,
                dropna=False
            )[metric_column].agg(["count", "sum", "mean"])

            grouped = grouped.round(2)

            answer = (
                f"Analysis of '{metric_column}' grouped by "
                f"'{group_column}':\n\n"
                + grouped.to_string()
            )

            result_context = {
                "group_column": str(group_column),
                "metric_column": str(metric_column),
                "result": grouped.to_dict()
            }

        else:
            grouped = df[group_column].value_counts(dropna=False)

            answer = (
                f"Record count grouped by '{group_column}':\n\n"
                + grouped.to_string()
            )

            result_context = {
                "group_column": str(group_column),
                "counts": grouped.to_dict()
            }

        return make_result(
            filename,
            answer,
            "Grouped the uploaded data using pandas.",
            result_context
        )

    # ========================================================
    # 7. MOST FREQUENT VALUE
    # ========================================================

    if any(
        phrase in q
        for phrase in [
            "most common",
            "most frequent",
            "occur most",
            "appears most",
            "popular category"
        ]
    ):
        column = find_matching_column(
            question,
            df,
            numeric_only=False
        )

        if column is None:
            return {
                "answer": (
                    "I could not identify the column. "
                    f"Available columns: {available_columns_message(df)}"
                ),
                "citations": []
            }

        counts = df[column].value_counts(dropna=True)

        if counts.empty:
            return make_result(
                filename,
                f"No valid values were found in '{column}'.",
                "Checked value frequencies."
            )

        value = counts.index[0]
        count = int(counts.iloc[0])

        return make_result(
            filename,
            f"The most frequent value in '{column}' is "
            f"'{value}', appearing {count:,} times.",
            f"Counted values in '{column}'.",
            {
                "column": str(column),
                "value": str(value),
                "count": count
            }
        )

    # ========================================================
    # 8. TOP N / BOTTOM N
    # ========================================================

    top_match = re.search(r"\btop\s+(\d+)", q)
    bottom_match = re.search(r"\bbottom\s+(\d+)", q)

    if top_match or bottom_match:

        match = top_match or bottom_match
        n = int(match.group(1))

        if n < 1 or n > 20:
            return {
                "answer": "Please request between 1 and 20 records.",
                "citations": []
            }

        # Explicitly explain missing age column.
        asks_age = bool(re.search(r"\bage\b|\byears old\b", q))

        has_age_column = any(
            normalize_text(column) in ["age", "customer age"]
            for column in df.columns
        )

        if asks_age and not has_age_column:
            return make_result(
                filename,
                f"The column 'age' was not found in {filename}. "
                f"Available columns: {available_columns_message(df)}",
                "Checked whether the requested age column exists.",
                {"available_columns": df.columns.tolist()}
            )

        column = find_matching_column(
            question,
            df,
            numeric_only=False
        )

        if column is None:
            return {
                "answer": (
                    "I could not identify the column for sorting. "
                    f"Available columns: {available_columns_message(df)}"
                ),
                "citations": []
            }

        numeric_values = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        # Numeric sorting
        if numeric_values.notna().any():

            if top_match:
                selected_indices = numeric_values.nlargest(n).index
                title = f"Top {n}"
            else:
                selected_indices = numeric_values.nsmallest(n).index
                title = f"Bottom {n}"

            result_df = df.loc[selected_indices].copy()

        else:
            # Date sorting
            date_values = pd.to_datetime(
                df[column],
                errors="coerce"
            )

            if not date_values.notna().any():
                return make_result(
                    filename,
                    f"Column '{column}' is not numeric or date-based, "
                    "so it cannot be ranked.",
                    f"Checked whether '{column}' contains numeric or date values.",
                    {"column": str(column)}
                )

            if top_match:
                selected_indices = date_values.nlargest(n).index
                title = f"Top {n} (latest)"
            else:
                selected_indices = date_values.nsmallest(n).index
                title = f"Bottom {n} (earliest)"

            result_df = df.loc[selected_indices].copy()

        result_df = result_df.head(n)

        return make_result(
            filename,
            f"{title} records by '{column}':\n\n"
            + format_table(result_df, max_rows=n),
            f"Sorted records using '{column}'.",
            {
                "column": str(column),
                "records": result_df.to_dict(orient="records")
            }
        )

    # ========================================================
    # 9. UNIQUE VALUES
    # ========================================================

    if any(
        phrase in q
        for phrase in [
            "unique values",
            "distinct values",
            "unique count",
            "distinct count",
            "how many different"
        ]
    ):
        column = find_matching_column(
            question,
            df,
            numeric_only=False
        )

        if column is None:
            return {
                "answer": (
                    "Please mention the column for which you want "
                    "the unique count. "
                    f"Available columns: {available_columns_message(df)}"
                ),
                "citations": []
            }

        count = int(df[column].nunique())

        return make_result(
            filename,
            f"Column '{column}' contains {count:,} unique values.",
            "Counted unique values.",
            {
                "column": str(column),
                "unique_count": count
            }
        )

    # ========================================================
    # 10. SUM / TOTAL
    # ========================================================

    if any(word in q.split() for word in ["total", "sum", "overall"]):

        column = find_matching_column(
            question,
            df,
            numeric_only=True
        )

        if column is None:
            return {
                "answer": (
                    "I could not identify the numeric column to calculate "
                    "the total. Please mention the column name."
                ),
                "citations": []
            }

        numeric_values = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        total = numeric_values.sum()

        return make_result(
            filename,
            f"The total of '{column}' is {format_number(total)}.",
            f"Calculated the sum of '{column}'.",
            {
                "column": str(column),
                "total": float(total)
            }
        )

    # ========================================================
    # 11. AVERAGE / MEAN / MEDIAN
    # ========================================================

    if any(word in q.split() for word in ["average", "mean", "median"]):

        column = find_matching_column(
            question,
            df,
            numeric_only=True
        )

        if column is None:
            return {
                "answer": (
                    "I could not identify the numeric column to calculate "
                    "the average. Please mention the column name."
                ),
                "citations": []
            }

        numeric_values = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        if numeric_values.notna().sum() == 0:
            return make_result(
                filename,
                f"No numeric values were found in '{column}'.",
                f"Checked numeric values in '{column}'."
            )

        if "median" in q.split():
            value = numeric_values.median()
            operation = "median"
        else:
            value = numeric_values.mean()
            operation = "average"

        return make_result(
            filename,
            f"The {operation} of '{column}' is {format_number(value)}.",
            f"Calculated the {operation} of '{column}'.",
            {
                "column": str(column),
                operation: float(value)
            }
        )

    # ========================================================
    # 12. MAXIMUM / HIGHEST
    # ========================================================

    if any(
        word in q.split()
        for word in ["highest", "maximum", "max", "largest"]
    ):
        column = find_matching_column(
            question,
            df,
            numeric_only=True
        )

        if column is None:
            return {
                "answer": (
                    "I could not identify the numeric column for the "
                    "maximum value. Please mention the column name."
                ),
                "citations": []
            }

        values = pd.to_numeric(df[column], errors="coerce")

        if values.notna().sum() == 0:
            return make_result(
                filename,
                f"No numeric values were found in '{column}'.",
                f"Checked numeric values in '{column}'."
            )

        maximum = values.max()
        row_index = values.idxmax()
        row_details = df.loc[row_index].to_dict()

        answer = (
            f"The highest value in '{column}' is "
            f"{format_number(maximum)}.\n\n"
            "Record details:\n"
            + "\n".join(
                f"{key}: {value}"
                for key, value in row_details.items()
            )
        )

        return make_result(
            filename,
            answer,
            f"Found the maximum value in '{column}'.",
            {
                "column": str(column),
                "maximum": float(maximum),
                "record": row_details
            }
        )

    # ========================================================
    # 13. MINIMUM / LOWEST
    # ========================================================

    if any(
        word in q.split()
        for word in ["lowest", "minimum", "min", "smallest"]
    ):
        column = find_matching_column(
            question,
            df,
            numeric_only=True
        )

        if column is None:
            return {
                "answer": (
                    "I could not identify the numeric column for the "
                    "minimum value. Please mention the column name."
                ),
                "citations": []
            }

        values = pd.to_numeric(df[column], errors="coerce")

        if values.notna().sum() == 0:
            return make_result(
                filename,
                f"No numeric values were found in '{column}'.",
                f"Checked numeric values in '{column}'."
            )

        minimum = values.min()
        row_index = values.idxmin()
        row_details = df.loc[row_index].to_dict()

        answer = (
            f"The lowest value in '{column}' is "
            f"{format_number(minimum)}.\n\n"
            "Record details:\n"
            + "\n".join(
                f"{key}: {value}"
                for key, value in row_details.items()
            )
        )

        return make_result(
            filename,
            answer,
            f"Found the minimum value in '{column}'.",
            {
                "column": str(column),
                "minimum": float(minimum),
                "record": row_details
            }
        )

    # ========================================================
    # 14. GENERAL FALLBACK
    # ========================================================

    numeric_columns = get_numeric_columns(df)

    return make_result(
        filename,
        (
            f"I loaded {filename} successfully.\n\n"
            f"Rows: {len(df):,}\n"
            f"Columns: {len(df.columns)}\n\n"
            f"Available columns:\n"
            f"{available_columns_message(df)}\n\n"
            f"Numeric columns:\n"
            f"{', '.join(str(col) for col in numeric_columns)}\n\n"
            "Try asking about totals, averages, maximums, minimums, "
            "top or bottom records, missing values, duplicates, "
            "most common values, unique values, or grouping."
        ),
        "Inspected the uploaded CSV structure.",
        {
            "rows": int(len(df)),
            "columns": df.columns.tolist(),
            "numeric_columns": numeric_columns
        }
    )
