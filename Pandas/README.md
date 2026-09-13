# Pandas

A comprehensive, production-focused Pandas reference and applied-project collection for backend engineers. Each section builds on the previous, progressing from core data structures to real-world pipeline engineering.

---

## What This Is

This playbook is not a beginner tutorial. It is a structured reference for engineers who work with data in Python and want to understand how to use Pandas correctly, efficiently, and reliably in production systems.

Every topic is covered at the level of depth required to apply it confidently in backend systems: ETL pipelines, REST API ingestion, reporting services, data validation layers, and large-scale batch processing.

---

## Learning Path

```text
01  Fundamentals
       ↓
02  Reading and Writing Data
       ↓
03  Selecting and Filtering
       ↓
04  Data Cleaning
       ↓
05  Data Transformation
       ↓
06  Grouping and Aggregation
       ↓
07  Combining Data
       ↓
08  Sorting, Ranking and Statistics
       ↓
09  Strings and Datetime
       ↓
10  Performance and Memory
       ↓
11  Backend and Data Engineering
       ↓
12  Interview Preparation
       ↓
13  Projects (applied end-to-end)
```

---

## Sections

### [01 — Fundamentals](01-%20Fundamentals/README.md)

The Pandas data model, Series and DataFrame construction, dtypes, missing values, indexing mechanics, and copy-vs-view semantics. Everything else depends on getting these right.

---

### [02 — Reading and Writing Data](02-%20Reading%20and%20Writing%20Data/README.md)

CSV, JSON, Excel, Parquet, SQL, HTML, and text file I/O. Read functions, write functions, dtype control at ingestion, parsers and converters, chunked reading for large files, compression, and encoding.

| Topic | File |
|---|---|
| CSV | [01- CSV.md](02-%20Reading%20and%20Writing%20Data/01-%20CSV.md) |
| JSON | [02- JSON.md](02-%20Reading%20and%20Writing%20Data/02-%20JSON.md) |
| Excel | [03- Excel.md](02-%20Reading%20and%20Writing%20Data/03-%20Excel.md) |
| Parquet | [04- Parquet.md](02-%20Reading%20and%20Writing%20Data/04-%20Parquet.md) |
| SQL | [05- Sql.md](02-%20Reading%20and%20Writing%20Data/05-%20Sql.md) |
| HTML | [06- Html.md](02-%20Reading%20and%20Writing%20Data/06-%20Html.md) |
| Text Files | [07- Text Files.md](02-%20Reading%20and%20Writing%20Data/07-%20Text%20Files.md) |
| Read Functions | [08- Read Functions.md](02-%20Reading%20and%20Writing%20Data/08-%20Read%20Functions.md) |
| Write Functions | [09- Write Functions.md](02-%20Reading%20and%20Writing%20Data/09-%20Write%20Functions.md) |
| Dtype Control | [10- Dtype Control.md](02-%20Reading%20and%20Writing%20Data/10-%20Dtype%20Control.md) |
| Parsing and Converters | [11- Parsing And Converters.md](02-%20Reading%20and%20Writing%20Data/11-%20Parsing%20And%20Converters.md) |
| Chunked Reading | [12- Chunked Reading.md](02-%20Reading%20and%20Writing%20Data/12-%20Chunked%20Reading.md) |
| Compression | [13- Compression.md](02-%20Reading%20and%20Writing%20Data/13-%20Compression.md) |
| Encoding | [14- Encoding.md](02-%20Reading%20and%20Writing%20Data/14-%20Encoding.md) |

---

### [03 — Selecting and Filtering](03-%20Selecting%20and%20Filtering/README.md)

Column selection, row selection, `.loc`, `.iloc`, `.at`, `.iat`, boolean filtering, multiple conditions, `.isin()`, `.query()`, filtering missing values, indexing and selection mechanics, and setting values.

| Topic | File |
|---|---|
| Selecting Columns | [01- Selecting Columns.md](03-%20Selecting%20and%20Filtering/01-%20Selecting%20Columns.md) |
| Selecting Rows | [02- Selecting Rows.md](03-%20Selecting%20and%20Filtering/02-%20Selecting%20Rows.md) |
| Loc | [03- Loc.md](03-%20Selecting%20and%20Filtering/03-%20Loc.md) |
| Iloc | [04- Iloc.md](03-%20Selecting%20and%20Filtering/04-%20Iloc.md) |
| At and Iat | [05- At And Iat.md](03-%20Selecting%20and%20Filtering/05-%20At%20And%20Iat.md) |
| Boolean Filtering | [06- Boolean Filtering.md](03-%20Selecting%20and%20Filtering/06-%20Boolean%20Filtering.md) |
| Multiple Conditions | [07- Multiple Conditions.md](03-%20Selecting%20and%20Filtering/07-%20Multiple%20Conditions.md) |
| Isin | [08- Isin.md](03-%20Selecting%20and%20Filtering/08-%20Isin.md) |
| Query | [09- Query.md](03-%20Selecting%20and%20Filtering/09-%20Query.md) |
| Filtering Missing Values | [10- Filtering Missing Values.md](03-%20Selecting%20and%20Filtering/10-%20Filtering%20Missing%20Values.md) |
| Indexing and Selection | [11- Indexing And Selection.md](03-%20Selecting%20and%20Filtering/11-%20Indexing%20And%20Selection.md) |
| Setting Values | [12- Setting Values.md](03-%20Selecting%20and%20Filtering/12-%20Setting%20Values.md) |

---

### [04 — Data Cleaning](04-%20Data%20Cleaning/README.md)

Data quality concepts, missing values, `.isna()` / `.notna()`, `.fillna()`, `.dropna()`, duplicate detection, `.drop_duplicates()`, inconsistent values, type conversion, numeric cleaning, string cleaning, datetime cleaning, outlier handling, and validation rules.

| Topic | File |
|---|---|
| Data Quality | [01- Data Quality.md](04-%20Data%20Cleaning/01-%20Data%20Quality.md) |
| Missing Values | [02- Missing Values.md](04-%20Data%20Cleaning/02-%20Missing%20Values.md) |
| Isna and Notna | [03- Isna And Notna.md](04-%20Data%20Cleaning/03-%20Isna%20And%20Notna.md) |
| Fillna | [04- Fillna.md](04-%20Data%20Cleaning/04-%20Fillna.md) |
| Dropna | [05- Dropna.md](04-%20Data%20Cleaning/05-%20Dropna.md) |
| Duplicate Data | [06- Duplicate Data.md](04-%20Data%20Cleaning/06-%20Duplicate%20Data.md) |
| Drop Duplicates | [07- Drop Duplicates.md](04-%20Data%20Cleaning/07-%20Drop%20Duplicates.md) |
| Inconsistent Values | [08- Inconsistent Values.md](04-%20Data%20Cleaning/08-%20Inconsistent%20Values.md) |
| Type Conversion | [09- Type Conversion.md](04-%20Data%20Cleaning/09-%20Type%20Conversion.md) |
| Numeric Cleaning | [10- Numeric Cleaning.md](04-%20Data%20Cleaning/10-%20Numeric%20Cleaning.md) |
| String Cleaning | [11- String Cleaning.md](04-%20Data%20Cleaning/11-%20String%20Cleaning.md) |
| Datetime Cleaning | [12- Datetime Cleaning.md](04-%20Data%20Cleaning/12-%20Datetime%20Cleaning.md) |
| Outlier Handling | [13- Outlier Handling.md](04-%20Data%20Cleaning/13-%20Outlier%20Handling.md) |
| Validation Rules | [14- Validation Rules.md](04-%20Data%20Cleaning/14-%20Validation%20Rules.md) |

---

### [05 — Data Transformation](05-%20Data%20Transformation/README.md)

Assignment and transformation patterns, renaming, `.astype()`, `.map()`, `.apply()`, element-wise operations, `.where()` / `.mask()`, `.replace()`, `.assign()`, `.melt()`, pivot and pivot table, `.cut()` / `.qcut()`, stack and unstack, `.explode()`, and categorical data.

| Topic | File |
|---|---|
| Assignment and Transformation | [01- Assignment And Transformation.md](05-%20Data%20Transformation/01-%20Assignment%20And%20Transformation.md) |
| Rename | [02- Rename.md](05-%20Data%20Transformation/02-%20Rename.md) |
| Astype | [03- Astype.md](05-%20Data%20Transformation/03-%20Astype.md) |
| Map | [04- Map.md](05-%20Data%20Transformation/04-%20Map.md) |
| Apply | [05- Apply.md](05-%20Data%20Transformation/05-%20Apply.md) |
| Applymap and Elementwise Operations | [06- Applymap And Elementwise Operations.md](05-%20Data%20Transformation/06-%20Applymap%20And%20Elementwise%20Operations.md) |
| Where and Mask | [08- Where And Mask.md](05-%20Data%20Transformation/08-%20Where%20And%20Mask.md) |
| Replace | [07- Replace.md](05-%20Data%20Transformation/07-%20Replace.md) |
| Assign | [09- Assign.md](05-%20Data%20Transformation/09-%20Assign.md) |
| Melt | [10- Melt.md](05-%20Data%20Transformation/10-%20Melt.md) |
| Pivot and Pivot Table | [11- Pivot And Pivot Table.md](05-%20Data%20Transformation/11-%20Pivot%20And%20Pivot%20Table.md) |
| Stack and Unstack | [12- Stack And Unstack.md](05-%20Data%20Transformation/12-%20Stack%20And%20Unstack.md) |
| Explode | [13- Explode.md](05-%20Data%20Transformation/13-%20Explode.md) |
| Cut and Qcut | [14- Cut And Qcut.md](05-%20Data%20Transformation/14-%20Cut%20And%20Qcut.md) |
| Categorical Data | [15- Categorical Data.md](05-%20Data%20Transformation/15-%20Categorical%20Data.md) |

---

### [06 — Grouping and Aggregation](06-%20Grouping%20and%20Aggregation/README.md)

`.groupby()`, group keys, aggregation functions, `.agg()`, `.transform()`, `.filter()`, named aggregation, multiple aggregations, grouped transformations, and hierarchical grouping.

| Topic | File |
|---|---|
| Groupby | [01- Groupby.md](06-%20Grouping%20and%20Aggregation/01-%20Groupby.md) |
| Groupby Keys | [02- Groupby Keys.md](06-%20Grouping%20and%20Aggregation/02-%20Groupby%20Keys.md) |
| Aggregation | [03- Aggregation.md](06-%20Grouping%20and%20Aggregation/03-%20Aggregation.md) |
| Agg | [04- Agg.md](06-%20Grouping%20and%20Aggregation/04-%20Agg.md) |
| Transform | [05- Transform.md](06-%20Grouping%20and%20Aggregation/05-%20Transform.md) |
| Filter | [06- Filter.md](06-%20Grouping%20and%20Aggregation/06-%20Filter.md) |
| Named Aggregation | [07- Named Aggregation.md](06-%20Grouping%20and%20Aggregation/07-%20Named%20Aggregation.md) |
| Multiple Aggregations | [08- Multiple Aggregations.md](06-%20Grouping%20and%20Aggregation/08-%20Multiple%20Aggregations.md) |
| Grouped Transformations | [09- Grouped Transformations.md](06-%20Grouping%20and%20Aggregation/09-%20Grouped%20Transformations.md) |
| Hierarchical Grouping | [10- Hierarchical Grouping.md](06-%20Grouping%20and%20Aggregation/10-%20Hierarchical%20Grouping.md) |

---

### [07 — Combining Data](07-%20Combining%20Data/README.md)

`.concat()`, `.merge()`, `.join()`, merge types (inner, left, right, outer, cross), merge validation, and handling duplicate keys.

| Topic | File |
|---|---|
| Concat | [01- Concat.md](07-%20Combining%20Data/01-%20Concat.md) |
| Merge | [02- Merge.md](07-%20Combining%20Data/02-%20Merge.md) |
| Join | [03- Join.md](07-%20Combining%20Data/03-%20Join.md) |
| Merge Types | [04- Merge Types.md](07-%20Combining%20Data/04-%20Merge%20Types.md) |
| Inner Join | [05- Inner Join.md](07-%20Combining%20Data/05-%20Inner%20Join.md) |
| Left Join | [06- Left Join.md](07-%20Combining%20Data/06-%20Left%20Join.md) |
| Right Join | [07- Right Join.md](07-%20Combining%20Data/07-%20Right%20Join.md) |
| Outer Join | [08- Outer Join.md](07-%20Combining%20Data/08-%20Outer%20Join.md) |
| Cross Join | [09- Cross Join.md](07-%20Combining%20Data/09-%20Cross%20Join.md) |
| Merge Validation | [10- Merge Validation.md](07-%20Combining%20Data/10-%20Merge%20Validation.md) |
| Duplicate Keys | [11- Duplicate Keys.md](07-%20Combining%20Data/11-%20Duplicate%20Keys.md) |

---

### [08 — Sorting Ranking and Statistics](08-%20Sorting%20Ranking%20and%20Statistics/README.md)

`.sort_values()`, `.sort_index()`, ranking, `.rank()`, descriptive statistics, sum/mean/median, min/max, `.count()` / `.nunique()`, `.value_counts()`, quantiles, correlation, covariance, and cumulative operations.

| Topic | File |
|---|---|
| Sort Values | [01- Sort Values.md](08-%20Sorting%20Ranking%20and%20Statistics/01-%20Sort%20Values.md) |
| Sort Index | [02- Sort Index.md](08-%20Sorting%20Ranking%20and%20Statistics/02-%20Sort%20Index.md) |
| Ranking | [03- Ranking.md](08-%20Sorting%20Ranking%20and%20Statistics/03-%20Ranking.md) |
| Rank | [04- Rank.md](08-%20Sorting%20Ranking%20and%20Statistics/04-%20Rank.md) |
| Descriptive Statistics | [05- Descriptive Statistics.md](08-%20Sorting%20Ranking%20and%20Statistics/05-%20Descriptive%20Statistics.md) |
| Sum Mean Median | [06- Sum Mean Median.md](08-%20Sorting%20Ranking%20and%20Statistics/06-%20Sum%20Mean%20Median.md) |
| Min Max | [07- Min Max.md](08-%20Sorting%20Ranking%20and%20Statistics/07-%20Min%20Max.md) |
| Count and Nunique | [08- Count And Nunique.md](08-%20Sorting%20Ranking%20and%20Statistics/08-%20Count%20And%20Nunique.md) |
| Value Counts | [09- Value Counts.md](08-%20Sorting%20Ranking%20and%20Statistics/09-%20Value%20Counts.md) |
| Quantiles | [10- Quantiles.md](08-%20Sorting%20Ranking%20and%20Statistics/10-%20Quantiles.md) |
| Correlation | [11- Correlation.md](08-%20Sorting%20Ranking%20and%20Statistics/11-%20Correlation.md) |
| Covariance | [12- Covariance.md](08-%20Sorting%20Ranking%20and%20Statistics/12-%20Covariance.md) |
| Cumulative Operations | [13- Cumulative Operations.md](08-%20Sorting%20Ranking%20and%20Statistics/13-%20Cumulative%20Operations.md) |

---

### [09 — Strings and Datetime](09-%20Strings%20and%20Datetime/README.md)

The `.str` accessor, string cleaning, search, extraction, regular expressions, datetime overview, `pd.to_datetime()`, datetime components, filtering by date, date offsets, timedeltas, timezone-aware datetimes, resampling, and time series indexing.

| Topic | File |
|---|---|
| String Accessor | [01- String Accessor.md](09-%20Strings%20and%20Datetime/01-%20String%20Accessor.md) |
| String Cleaning | [02- String Cleaning.md](09-%20Strings%20and%20Datetime/02-%20String%20Cleaning.md) |
| String Search | [03- String Search.md](09-%20Strings%20and%20Datetime/03-%20String%20Search.md) |
| String Extraction | [04- String Extraction.md](09-%20Strings%20and%20Datetime/04-%20String%20Extraction.md) |
| Regular Expressions | [05- Regular Expressions.md](09-%20Strings%20and%20Datetime/05-%20Regular%20Expressions.md) |
| Datetime Overview | [06- Datetime Overview.md](09-%20Strings%20and%20Datetime/06-%20Datetime%20Overview.md) |
| To Datetime | [07- To Datetime.md](09-%20Strings%20and%20Datetime/07-%20To%20Datetime.md) |
| Datetime Components | [08- Datetime Components.md](09-%20Strings%20and%20Datetime/08-%20Datetime%20Components.md) |
| Datetime Filtering | [09- Datetime Filtering.md](09-%20Strings%20and%20Datetime/09-%20Datetime%20Filtering.md) |
| Date Offsets | [10- Date Offsets.md](09-%20Strings%20and%20Datetime/10-%20Date%20Offsets.md) |
| Timedeltas | [11- Timedeltas.md](09-%20Strings%20and%20Datetime/11-%20Timedeltas.md) |
| Timezone Aware Datetime | [12- Timezone Aware Datetime.md](09-%20Strings%20and%20Datetime/12-%20Timezone%20Aware%20Datetime.md) |
| Resampling | [13- Resampling.md](09-%20Strings%20and%20Datetime/13-%20Resampling.md) |
| Time Series Indexing | [14- Time Series Indexing.md](09-%20Strings%20and%20Datetime/14-%20Time%20Series%20Indexing.md) |

---

### [10 — Performance and Memory](10-%20Performance%20and%20Memory/README.md)

Pandas performance model, vectorization, apply vs. vectorization, efficient dtypes, categorical dtype, memory usage, memory optimization, copy vs. view, avoiding unnecessary copies, efficient filtering, efficient groupby, efficient joins, chunk processing, and Parquet for performance.

| Topic | File |
|---|---|
| Pandas Performance | [01- Pandas Performance.md](10-%20Performance%20and%20Memory/01-%20Pandas%20Performance.md) |
| Vectorization | [02- Vectorization.md](10-%20Performance%20and%20Memory/02-%20Vectorization.md) |
| Apply vs Vectorization | [03- Apply Vs Vectorization.md](10-%20Performance%20and%20Memory/03-%20Apply%20Vs%20Vectorization.md) |
| Efficient Dtypes | [04- Efficient Dtypes.md](10-%20Performance%20and%20Memory/04-%20Efficient%20Dtypes.md) |
| Categorical Dtype | [05- Categorical Dtype.md](10-%20Performance%20and%20Memory/05-%20Categorical%20Dtype.md) |
| Memory Usage | [06- Memory Usage.md](10-%20Performance%20and%20Memory/06-%20Memory%20Usage.md) |
| Memory Optimization | [07- Memory Optimization.md](10-%20Performance%20and%20Memory/07-%20Memory%20Optimization.md) |
| Copy vs View | [08- Copy Vs View.md](10-%20Performance%20and%20Memory/08-%20Copy%20Vs%20View.md) |
| Avoiding Unnecessary Copies | [09- Avoiding Unnecessary Copies.md](10-%20Performance%20and%20Memory/09-%20Avoiding%20Unnecessary%20Copies.md) |
| Efficient Filtering | [10- Efficient Filtering.md](10-%20Performance%20and%20Memory/10-%20Efficient%20Filtering.md) |
| Efficient Groupby | [11- Efficient Groupby.md](10-%20Performance%20and%20Memory/11-%20Efficient%20Groupby.md) |
| Efficient Joins | [12- Efficient Joins.md](10-%20Performance%20and%20Memory/12-%20Efficient%20Joins.md) |
| Chunk Processing | [13- Chunk Processing.md](10-%20Performance%20and%20Memory/13-%20Chunk%20Processing.md) |
| Parquet Performance | [14- Parquet Performance.md](10-%20Performance%20and%20Memory/14-%20Parquet%20Performance.md) |

---

### [11 — Backend and Data Engineering](11-%20Backend%20and%20Data%20Engineering/README.md)

Pandas in ETL systems, Pandas and SQL, loading from databases, writing to databases, Pandas and Parquet, large dataset processing patterns, chunk processing, data validation, data quality checks, batch processing, incremental processing, and idempotent data processing.

| Topic | File |
|---|---|
| Pandas in ETL | [01- Pandas In Etl.md](11-%20Backend%20and%20Data%20Engineering/01-%20Pandas%20In%20Etl.md) |
| Pandas and SQL | [02- Pandas And Sql.md](11-%20Backend%20and%20Data%20Engineering/02-%20Pandas%20And%20Sql.md) |
| Database to DataFrame | [03- Database To Dataframe.md](11-%20Backend%20and%20Data%20Engineering/03-%20Database%20To%20Dataframe.md) |
| DataFrame to Database | [04- Dataframe To Database.md](11-%20Backend%20and%20Data%20Engineering/04-%20Dataframe%20To%20Database.md) |
| Pandas and Parquet | [05- Pandas And Parquet.md](11-%20Backend%20and%20Data%20Engineering/05-%20Pandas%20And%20Parquet.md) |
| Large Dataset Processing | [06- Large Dataset Processing.md](11-%20Backend%20and%20Data%20Engineering/06-%20Large%20Dataset%20Processing.md) |
| Chunk Processing | [07- Chunk Processing.md](11-%20Backend%20and%20Data%20Engineering/07-%20Chunk%20Processing.md) |
| Data Validation | [08- Data Validation.md](11-%20Backend%20and%20Data%20Engineering/08-%20Data%20Validation.md) |
| Data Quality Checks | [09- Data Quality Checks.md](11-%20Backend%20and%20Data%20Engineering/09-%20Data%20Quality%20Checks.md) |
| Batch Processing | [10- Batch Processing.md](11-%20Backend%20and%20Data%20Engineering/10-%20Batch%20Processing.md) |
| Incremental Processing | [11- Incremental Processing.md](11-%20Backend%20and%20Data%20Engineering/11-%20Incremental%20Processing.md) |
| Idempotent Data Processing | [12- Idempotent Data Processing.md](11-%20Backend%20and%20Data%20Engineering/12-%20Idempotent%20Data%20Processing.md) |

---

### [12 — Interview Preparation](12-%20Interview%20Preparation/README.md)

Targeted interview preparation covering Pandas fundamentals, Series and DataFrame concepts, indexing, filtering, missing values, duplicates, cleaning, apply/map/transform, groupby, merge/join, concat, pivot/melt, strings and datetime, performance, memory optimization, Pandas and SQL, ETL scenarios, data cleaning scenarios, data transformation scenarios, reporting scenarios, debugging Pandas, and coding problems.

| Topic | File |
|---|---|
| Pandas Fundamentals | [01- Pandas Fundamentals.md](12-%20Interview%20Preparation/01-%20Pandas%20Fundamentals.md) |
| Series and DataFrame | [02- Series And Dataframe.md](12-%20Interview%20Preparation/02-%20Series%20And%20Dataframe.md) |
| Indexing and Selection | [03- Indexing And Selection.md](12-%20Interview%20Preparation/03-%20Indexing%20And%20Selection.md) |
| Loc and Iloc | [04- Loc And Iloc.md](12-%20Interview%20Preparation/04-%20Loc%20And%20Iloc.md) |
| Filtering | [05- Filtering.md](12-%20Interview%20Preparation/05-%20Filtering.md) |
| Missing Values | [06- Missing Values.md](12-%20Interview%20Preparation/06-%20Missing%20Values.md) |
| Duplicates | [07- Duplicates.md](12-%20Interview%20Preparation/07-%20Duplicates.md) |
| Data Cleaning | [08- Data Cleaning.md](12-%20Interview%20Preparation/08-%20Data%20Cleaning.md) |
| Apply Map and Transform | [09- Apply Map And Transform.md](12-%20Interview%20Preparation/09-%20Apply%20Map%20And%20Transform.md) |
| Groupby and Aggregation | [10- Groupby And Aggregation.md](12-%20Interview%20Preparation/10-%20Groupby%20And%20Aggregation.md) |
| Merge and Join | [11- Merge And Join.md](12-%20Interview%20Preparation/11-%20Merge%20And%20Join.md) |
| Concat | [12- Concat.md](12-%20Interview%20Preparation/12-%20Concat.md) |
| Pivot and Melt | [13- Pivot And Melt.md](12-%20Interview%20Preparation/13-%20Pivot%20And%20Melt.md) |
| Strings and Datetime | [14- Strings And Datetime.md](12-%20Interview%20Preparation/14-%20Strings%20And%20Datetime.md) |
| Pandas Performance | [15- Pandas Performance.md](12-%20Interview%20Preparation/15-%20Pandas%20Performance.md) |
| Memory Optimization | [16- Memory Optimization.md](12-%20Interview%20Preparation/16-%20Memory%20Optimization.md) |
| Pandas and SQL | [17- Pandas And Sql.md](12-%20Interview%20Preparation/17-%20Pandas%20And%20Sql.md) |
| ETL Scenarios | [18- ETL Scenarios.md](12-%20Interview%20Preparation/18-%20ETL%20Scenarios.md) |
| Data Cleaning Scenarios | [19- Data Cleaning Scenarios.md](12-%20Interview%20Preparation/19-%20Data%20Cleaning%20Scenarios.md) |
| Data Transformation Scenarios | [20- Data Transformation Scenarios.md](12-%20Interview%20Preparation/20-%20Data%20Transformation%20Scenarios.md) |
| Reporting Scenarios | [21- Reporting Scenarios.md](12-%20Interview%20Preparation/21-%20Reporting%20Scenarios.md) |
| Debugging Pandas | [22- Debugging Pandas.md](12-%20Interview%20Preparation/22-%20Debugging%20Pandas.md) |
| Pandas Coding Problems | [23- Pandas Coding Problems.md](12-%20Interview%20Preparation/23-%20Pandas%20Coding%20Problems.md) |

---

### [13 — Projects](13-%20Projects/README.md)

Applied end-to-end projects that combine the skills from all previous sections.

| Project | Description |
|---|---|
| [01 — E-Commerce Data Pipeline](13-%20Projects/01-%20E-Commerce%20Data%20Pipeline/README.md) | Chunked CSV ingestion · validation · enrichment joins · multi-level aggregation · reconciliation · atomic Parquet reports |
| [02 — API Data Processing Pipeline](13-%20Projects/02-%20API%20Data%20Processing%20Pipeline/README.md) | Authenticated REST API · retries with backoff · pagination · JSON normalization · schema validation · atomic Parquet output |
| [03 — Large Dataset Processing](13-%20Projects/03-%20Large%20Dataset%20Processing/README.md) | Memory-efficient chunked processing · column projection · categorical dtypes · checkpointing · partition writes · benchmarks |
