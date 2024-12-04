import pytest
from dbt.tests.util import run_dbt, get_connection, rm_file, write_file
from tests.utils.util import relation_from_name
from tests.fixtures.profiles import unique_schema, dbt_profile_data

cursor_early_exit_model = """
{{ config(materialized='table') }}

WITH numbers AS (
    SELECT row_number() OVER () AS id
    FROM (
        SELECT 1 FROM (VALUES (1)) AS t1(n)
        CROSS JOIN (VALUES (1)) AS t2(n)
        CROSS JOIN (VALUES (1)) AS t3(n)
        CROSS JOIN (VALUES (1)) AS t4(n)
        CROSS JOIN (VALUES (1)) AS t5(n)
        CROSS JOIN (VALUES (1)) AS t6(n)
        CROSS JOIN (VALUES (1)) AS t7(n)
        CROSS JOIN (VALUES (1)) AS t8(n)
        CROSS JOIN (VALUES (1)) AS t9(n)
        CROSS JOIN (VALUES (1)) AS t10(n)
    ) AS derived
)
INSERT INTO your_schema.test_table (id)
SELECT id
FROM numbers
WHERE id <= 1000000;
"""

class TestCursorEarlyExitDremio:
    @pytest.fixture(scope="class")
    def models(self):
        return {
            "test_cursor_early_exit.sql": cursor_early_exit_model,
        }

    def test_insert_one_million_rows(self, project):
        # Run the dbt model to insert 1 million rows
        run_dbt(["run", "--select", "test_cursor_early_exit"])

        relation = relation_from_name(project.adapter, "test_table")

        rm_file(project.project_root, "models", "test_cursor_early_exit.sql")

        with get_connection(project.adapter) as connection:
            result = connection.execute("SELECT COUNT(*) FROM {}".format(relation))
            row_count = result.fetchone()[0]

        # I want this to error on purpose for testing purposes
        assert row_count == 123, f"Expected 123 rows, but got {row_count}"