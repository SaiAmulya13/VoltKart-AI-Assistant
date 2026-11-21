
import pytest

from backend.services.multi_csv_service import (
    answer_multi_csv_question,
    build_multi_csv_dataset,
)


def test_dataset_is_not_empty():
    df = build_multi_csv_dataset()

    assert not df.empty


def test_dataset_contains_required_columns():
    df = build_multi_csv_dataset()

    required_columns = [
        "order_id",
        "product_id",
        "customer_id",
        "store_name",
        "net_revenue_inr",
        "is_returned",
    ]

    for column in required_columns:
        assert column in df.columns


def test_net_revenue_is_not_negative():
    df = build_multi_csv_dataset()

    assert (df["net_revenue_inr"] >= 0).all()


def test_top_store_question():
    result = answer_multi_csv_question(
        "Which store generated the highest revenue?"
    )

    assert result is not None
    assert "answer" in result
    assert "sources" in result
    assert "Connaught Place" in result["answer"]


def test_top_products_question():
    result = answer_multi_csv_question(
        "Which products have the highest sales?"
    )

    assert result is not None
    assert "answer" in result


def test_returned_items_question():
    result = answer_multi_csv_question(
        "How many products were returned?"
    )

    assert result is not None
    assert "answer" in result
def test_revenue_by_city_question():
    result = answer_multi_csv_question(
        "What is the total revenue by city?"
    )

    assert result is not None
    assert "answer" in result
    assert "Delhi" in result["answer"]
    assert "Hyderabad" in result["answer"]

def test_revenue_by_category_question():
    result = answer_multi_csv_question(
        "Which product category generated the highest revenue?"
    )

    assert result is not None
    assert "answer" in result
    assert "category" in result["answer"].lower()

def test_average_order_value_question():
    result = answer_multi_csv_question(
        "What is the average order value?"
    )

    assert result is not None
    assert "answer" in result
    assert "average order value" in result["answer"].lower()


def test_revenue_by_year_question():
    answer = answer_multi_csv_question(
        "What was the total revenue in 2025?"
    )

    if isinstance(answer, dict):
        answer = answer.get("answer", "")

    assert "revenue" in answer.lower()


def test_monthly_revenue_question():
    answer = answer_multi_csv_question(
        "Show monthly revenue"
    )

    if isinstance(answer, dict):
        answer = answer.get("answer", "")

    assert "revenue" in answer.lower()


def test_revenue_by_month_question():
    answer = answer_multi_csv_question(
        "What was the revenue in January 2025?"
    )

    if isinstance(answer, dict):
        answer = answer.get("answer", "")

    assert "revenue" in answer.lower()
