from tests.dialects.test_dialect import Validator


class TestSpark(Validator):
    dialect = "spark"

    def test_ddl(self):
        self.validate_all(
            "CREATE TABLE db.example_table (col_a struct<struct_col_a:int, struct_col_b:string>)",
            write={
                "presto": "CREATE TABLE db.example_table (col_a ROW(struct_col_a INTEGER, struct_col_b VARCHAR))",
                "hive": "CREATE TABLE db.example_table (col_a STRUCT<struct_col_a INT, struct_col_b STRING>)",
                "spark": "CREATE TABLE db.example_table (col_a STRUCT<struct_col_a: INT, struct_col_b: STRING>)",
            },
        )
        self.validate_all(
            "CREATE TABLE db.example_table (col_a struct<struct_col_a:int, struct_col_b:struct<nested_col_a:string, nested_col_b:string>>)",
            write={
                "bigquery": "CREATE TABLE db.example_table (col_a STRUCT<struct_col_a INT64, struct_col_b STRUCT<nested_col_a STRING, nested_col_b STRING>>)",
                "presto": "CREATE TABLE db.example_table (col_a ROW(struct_col_a INTEGER, struct_col_b ROW(nested_col_a VARCHAR, nested_col_b VARCHAR)))",
                "hive": "CREATE TABLE db.example_table (col_a STRUCT<struct_col_a INT, struct_col_b STRUCT<nested_col_a STRING, nested_col_b STRING>>)",
                "spark": "CREATE TABLE db.example_table (col_a STRUCT<struct_col_a: INT, struct_col_b: STRUCT<nested_col_a: STRING, nested_col_b: STRING>>)",
            },
        )
        self.validate_all(
            "CREATE TABLE db.example_table (col_a array<int>, col_b array<array<int>>)",
            write={
                "bigquery": "CREATE TABLE db.example_table (col_a ARRAY<INT64>, col_b ARRAY<ARRAY<INT64>>)",
                "presto": "CREATE TABLE db.example_table (col_a ARRAY(INTEGER), col_b ARRAY(ARRAY(INTEGER)))",
                "hive": "CREATE TABLE db.example_table (col_a ARRAY<INT>, col_b ARRAY<ARRAY<INT>>)",
                "spark": "CREATE TABLE db.example_table (col_a ARRAY<INT>, col_b ARRAY<ARRAY<INT>>)",
            },
        )
        self.validate_all(
            "CREATE TABLE x USING ICEBERG PARTITIONED BY (MONTHS(y)) LOCATION 's3://z'",
            write={
                "presto": "CREATE TABLE x WITH (TABLE_FORMAT = 'ICEBERG', PARTITIONED_BY = ARRAY['MONTHS'])",
                "hive": "CREATE TABLE x USING ICEBERG PARTITIONED BY (MONTHS(y)) LOCATION 's3://z'",
                "spark": "CREATE TABLE x USING ICEBERG PARTITIONED BY (MONTHS(y)) LOCATION 's3://z'",
            },
        )
        self.validate_all(
            "CREATE TABLE test STORED AS PARQUET AS SELECT 1",
            write={
                "presto": "CREATE TABLE test WITH (FORMAT = 'PARQUET') AS SELECT 1",
                "hive": "CREATE TABLE test STORED AS PARQUET AS SELECT 1",
                "spark": "CREATE TABLE test STORED AS PARQUET AS SELECT 1",
            },
        )
        self.validate_all(
            "CREATE TABLE test USING ICEBERG STORED AS PARQUET AS SELECT 1",
            write={
                "presto": "CREATE TABLE test WITH (TABLE_FORMAT = 'ICEBERG', FORMAT = 'PARQUET') AS SELECT 1",
                "hive": "CREATE TABLE test USING ICEBERG STORED AS PARQUET AS SELECT 1",
                "spark": "CREATE TABLE test USING ICEBERG STORED AS PARQUET AS SELECT 1",
            },
        )
        self.validate_all(
            """CREATE TABLE blah (col_a INT) COMMENT "Test comment: blah" PARTITIONED BY (date STRING) STORED AS ICEBERG TBLPROPERTIES('x' = '1')""",
            write={
                "presto": """CREATE TABLE blah (
  col_a INTEGER,
  date VARCHAR
)
COMMENT='Test comment: blah'
WITH (
  PARTITIONED_BY = ARRAY['date'],
  FORMAT = 'ICEBERG',
  x = '1'
)""",
                "hive": """CREATE TABLE blah (
  col_a INT
)
COMMENT 'Test comment: blah'
PARTITIONED BY (
  date STRING
)
STORED AS ICEBERG
TBLPROPERTIES (
  'x' = '1'
)""",
                "spark": """CREATE TABLE blah (
  col_a INT
)
COMMENT 'Test comment: blah'
PARTITIONED BY (
  date STRING
)
STORED AS ICEBERG
TBLPROPERTIES (
  'x' = '1'
)""",
            },
            pretty=True,
        )

    def test_to_date(self):
        self.validate_all(
            "TO_DATE(x, 'yyyy-MM-dd')",
            write={
                "duckdb": "CAST(x AS DATE)",
                "hive": "TO_DATE(x)",
                "presto": "CAST(SUBSTR(CAST(x AS VARCHAR), 1, 10) AS DATE)",
                "spark": "TO_DATE(x)",
            },
        )
        self.validate_all(
            "TO_DATE(x, 'yyyy')",
            write={
                "duckdb": "CAST(STRPTIME(x, '%Y') AS DATE)",
                "hive": "TO_DATE(x, 'yyyy')",
                "presto": "CAST(DATE_PARSE(x, '%Y') AS DATE)",
                "spark": "TO_DATE(x, 'yyyy')",
            },
        )

    def test_hint(self):
        self.validate_all(
            "SELECT /*+ COALESCE(3) */ * FROM x",
            write={
                "spark": "SELECT /*+ COALESCE(3) */ * FROM x",
            },
        )
        self.validate_all(
            "SELECT /*+ COALESCE(3), REPARTITION(1) */ * FROM x",
            write={
                "spark": "SELECT /*+ COALESCE(3), REPARTITION(1) */ * FROM x",
            },
        )

    def test_spark(self):
        self.validate_all(
            "ARRAY_SORT(x, (left, right) -> -1)",
            write={
                "duckdb": "ARRAY_SORT(x)",
                "presto": "ARRAY_SORT(x, (left, right) -> -1)",
                "hive": "SORT_ARRAY(x)",
                "spark": "ARRAY_SORT(x, (left, right) -> -1)",
            },
        )
        self.validate_all(
            "ARRAY(0, 1, 2)",
            write={
                "bigquery": "[0, 1, 2]",
                "duckdb": "LIST_VALUE(0, 1, 2)",
                "presto": "ARRAY[0, 1, 2]",
                "hive": "ARRAY(0, 1, 2)",
                "spark": "ARRAY(0, 1, 2)",
            },
        )
        self.validate_all(
            "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname ASC NULLS LAST, lname",
            write={
                "duckdb": "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname NULLS LAST, lname",
                "postgres": "SELECT fname, lname, age FROM person ORDER BY age DESC, fname, lname NULLS FIRST",
                "presto": "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname, lname NULLS FIRST",
                "hive": "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname NULLS LAST, lname",
                "spark": "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname NULLS LAST, lname",
            },
        )
        self.validate_all(
            "SELECT APPROX_COUNT_DISTINCT(a) FROM foo",
            write={
                "duckdb": "SELECT APPROX_COUNT_DISTINCT(a) FROM foo",
                "presto": "SELECT APPROX_DISTINCT(a) FROM foo",
                "hive": "SELECT APPROX_COUNT_DISTINCT(a) FROM foo",
                "spark": "SELECT APPROX_COUNT_DISTINCT(a) FROM foo",
            },
        )
        self.validate_all(
            "MONTH('2021-03-01')",
            write={
                "duckdb": "MONTH(CAST('2021-03-01' AS DATE))",
                "presto": "MONTH(CAST(SUBSTR(CAST('2021-03-01' AS VARCHAR), 1, 10) AS DATE))",
                "hive": "MONTH(TO_DATE('2021-03-01'))",
                "spark": "MONTH(TO_DATE('2021-03-01'))",
            },
        )
        self.validate_all(
            "YEAR('2021-03-01')",
            write={
                "duckdb": "YEAR(CAST('2021-03-01' AS DATE))",
                "presto": "YEAR(CAST(SUBSTR(CAST('2021-03-01' AS VARCHAR), 1, 10) AS DATE))",
                "hive": "YEAR(TO_DATE('2021-03-01'))",
                "spark": "YEAR(TO_DATE('2021-03-01'))",
            },
        )
        self.validate_all(
            "'\u6bdb'",
            write={
                "duckdb": "'毛'",
                "presto": "'毛'",
                "hive": "'毛'",
                "spark": "'毛'",
            },
        )
        self.validate_all(
            "SELECT LEFT(x, 2), RIGHT(x, 2)",
            write={
                "duckdb": "SELECT SUBSTRING(x, 1, 2), SUBSTRING(x, LENGTH(x) - 2 + 1, 2)",
                "presto": "SELECT SUBSTRING(x, 1, 2), SUBSTRING(x, LENGTH(x) - 2 + 1, 2)",
                "hive": "SELECT SUBSTRING(x, 1, 2), SUBSTRING(x, LENGTH(x) - 2 + 1, 2)",
                "spark": "SELECT SUBSTRING(x, 1, 2), SUBSTRING(x, LENGTH(x) - 2 + 1, 2)",
            },
        )
        self.validate_all(
            "MAP_FROM_ARRAYS(ARRAY(1), c)",
            write={
                "duckdb": "MAP(LIST_VALUE(1), c)",
                "presto": "MAP(ARRAY[1], c)",
                "hive": "MAP(ARRAY(1), c)",
                "spark": "MAP_FROM_ARRAYS(ARRAY(1), c)",
            },
        )
        self.validate_all(
            "SELECT ARRAY_SORT(x)",
            write={
                "duckdb": "SELECT ARRAY_SORT(x)",
                "presto": "SELECT ARRAY_SORT(x)",
                "hive": "SELECT SORT_ARRAY(x)",
                "spark": "SELECT ARRAY_SORT(x)",
            },
        )