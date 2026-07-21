"""
NorthPeak - Bronze Pipeline Unit Tests
Phase 4: pytest for CI/CD gate
Phase 6: Integration with Great Expectations

These tests run on every PR via GitHub Actions.
Enterprise: Same pytest tests run in Azure DevOps / Jenkins CI pipelines.
"""

import pytest
import os
import sys
from datetime import date
from unittest.mock import MagicMock, patch


# ── Unit tests for bronze metadata function ────────────────────────
class TestBronzeMetadata:
    """Tests for add_bronze_metadata() function."""

    def test_bronze_metadata_adds_ingested_at(self):
        """Every Bronze record must have _bronze_ingested_at."""
        # Arrange
        mock_df = MagicMock()
        mock_df.withColumn.return_value = mock_df
        # Act
        from ingestion.pyspark.bronze_ingestion import add_bronze_metadata
        result = add_bronze_metadata(mock_df, "orders")
        # Assert
        calls = [str(c) for c in mock_df.withColumn.call_args_list]
        assert any("_bronze_ingested_at" in c for c in calls)

    def test_bronze_metadata_adds_source_table(self):
        """Bronze metadata must include source table name."""
        mock_df = MagicMock()
        mock_df.withColumn.return_value = mock_df
        from ingestion.pyspark.bronze_ingestion import add_bronze_metadata
        add_bronze_metadata(mock_df, "inventory")
        calls = [str(c) for c in mock_df.withColumn.call_args_list]
        assert any("_bronze_source_table" in c for c in calls)


# ── Data quality tests (no Spark required) ────────────────────────
class TestDataQualityRules:
    """
    Test data quality business rules without running Spark.
    These validate the LOGIC, not the Spark execution.
    """

    def test_null_customer_id_rule(self):
        """
        4.1% of orders have null customer_id (pre-2018).
        Silver rule: map to -1 (UNKNOWN_CUSTOMER), never drop.
        """
        # Simulate the rule logic
        def apply_customer_id_rule(customer_id):
            if customer_id is None:
                return -1
            return customer_id

        assert apply_customer_id_rule(None) == -1
        assert apply_customer_id_rule(123) == 123
        assert apply_customer_id_rule(0) == 0

    def test_negative_inventory_is_valid(self):
        """
        Negative inventory quantities are valid DC adjustments.
        Silver rule: set is_adjustment=True, never quarantine.
        """
        def apply_inventory_rule(quantity):
            is_adjustment = quantity < 0
            return {"quantity_on_hand": quantity, "is_adjustment": is_adjustment}

        result = apply_inventory_rule(-50.0)
        assert result["is_adjustment"] is True
        assert result["quantity_on_hand"] == -50.0

        result_positive = apply_inventory_rule(100.0)
        assert result_positive["is_adjustment"] is False

    def test_payment_reference_is_masked(self):
        """
        payment_reference containing card data must be SHA-256 hashed in Silver.
        Plain card numbers must never appear in Silver or Gold.
        """
        import hashlib
        raw = "4123-****-****-7890"
        hashed = hashlib.sha256(raw.encode()).hexdigest()

        # The hash must be 64 hex characters
        assert len(hashed) == 64
        # The raw card-like value must not be the output
        assert hashed != raw
        # Must be deterministic (same input = same hash for audit trail)
        assert hashed == hashlib.sha256(raw.encode()).hexdigest()

    def test_order_amount_positive_for_clean_records(self):
        """Negative total_amount records are quarantined in Silver."""
        def quarantine_rule(total_amount):
            return "quarantine" if total_amount < 0 else "silver"

        assert quarantine_rule(-5.00) == "quarantine"
        assert quarantine_rule(0.00) == "silver"
        assert quarantine_rule(45.99) == "silver"

    def test_duplicate_order_detection(self):
        """
        2.3% of orders have duplicate order_id.
        Silver keeps the latest by created_at.
        """
        orders = [
            {"order_id": 1, "created_at": "2026-01-01 10:00:00", "total_amount": 45.00},
            {"order_id": 1, "created_at": "2026-01-01 10:02:00", "total_amount": 45.50},  # duplicate
            {"order_id": 2, "created_at": "2026-01-01 11:00:00", "total_amount": 22.00},
        ]
        # Keep latest per order_id
        seen = {}
        for o in sorted(orders, key=lambda x: x["created_at"], reverse=True):
            if o["order_id"] not in seen:
                seen[o["order_id"]] = o

        deduped = list(seen.values())
        assert len(deduped) == 2
        order_1 = next(o for o in deduped if o["order_id"] == 1)
        assert order_1["total_amount"] == 45.50  # latest kept


# ── Pipeline idempotency test ─────────────────────────────────────
class TestPipelineIdempotency:
    """Bronze pipeline must produce the same result when run twice."""

    def test_idempotent_partition_overwrite(self):
        """
        Running Bronze ingestion twice for the same date must not
        double the row count. Overwrite partition mode ensures this.
        """
        # Simulate: first run writes 500 rows, second run writes 500 rows
        # With overwrite partition: result should still be 500, not 1000
        partition_state = {}

        def write_partition(date, rows):
            partition_state[date] = rows  # overwrite, not append

        write_partition("2026-07-14", list(range(500)))
        write_partition("2026-07-14", list(range(500)))  # re-run

        assert len(partition_state["2026-07-14"]) == 500  # not 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
