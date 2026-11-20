-- Amazon Athena query examples for the S3 event data lake.
--
-- Glue catalog defaults:
--   Database: data_lake_events
--   Table:    events
--
-- Expected table columns:
--   event_id, event_timestamp, tenant_id, event_type, user_id,
--   amount, currency, source, attributes, event_date
--
-- Partition key:
--   event_date (STRING, YYYY-MM-DD)
--
-- Run these statements in Amazon Athena after the Glue database and
-- external table have been created and the S3 dataset has been ingested.
--
-- Important:
--   1. Replace database/table identifiers if your deployment overrides
--      GLUE_DATABASE_NAME or GLUE_TABLE_NAME.
--   2. Register or project S3 partitions before relying on partition filters.
--   3. Athena SQL is read-only against this external table unless you
--      explicitly execute CTAS or INSERT statements.
--   4. The sample dataset stores amount as STRING. Cast it to DECIMAL
--      before performing numeric calculations.
--   5. The attributes column is declared as MAP<STRING, STRING> in the
--      current Glue table definition. Mixed JSON values, such as numeric
--      quantity values, may require schema normalization before querying.


-- ============================================================================
-- 1. Inspect the table schema
-- ============================================================================

DESCRIBE data_lake_events.events;


-- ============================================================================
-- 2. Inspect table properties and storage location
-- ============================================================================

SHOW CREATE TABLE data_lake_events.events;


-- ============================================================================
-- 3. Preview recent event records
-- ============================================================================

SELECT
    event_id,
    event_timestamp,
    event_date,
    tenant_id,
    event_type,
    user_id,
    amount,
    currency,
    source
FROM data_lake_events.events
ORDER BY event_timestamp DESC
LIMIT 20;


-- ============================================================================
-- 4. Count events by event type
-- ============================================================================

SELECT
    event_type,
    COUNT(*) AS event_count
FROM data_lake_events.events
GROUP BY event_type
ORDER BY event_count DESC;


-- ============================================================================
-- 5. Count events by ingestion partition date
-- ============================================================================

SELECT
    event_date,
    COUNT(*) AS event_count
FROM data_lake_events.events
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-07'
GROUP BY event_date
ORDER BY event_date;


-- ============================================================================
-- 6. Analyze event volume by source
-- ============================================================================

SELECT
    source,
    COUNT(*) AS total_events,
    COUNT(DISTINCT tenant_id) AS distinct_tenants,
    COUNT(DISTINCT user_id) AS distinct_users
FROM data_lake_events.events
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-07'
GROUP BY source
ORDER BY total_events DESC;


-- ============================================================================
-- 7. Analyze purchase events
-- ============================================================================

SELECT
    event_date,
    currency,
    COUNT(*) AS purchase_count,
    SUM(TRY_CAST(amount AS DECIMAL(18, 2))) AS purchase_amount
FROM data_lake_events.events
WHERE event_type = 'purchase'
  AND event_date BETWEEN '2026-01-01' AND '2026-01-07'
GROUP BY
    event_date,
    currency
ORDER BY
    event_date,
    currency;


-- ============================================================================
-- 8. Calculate net transaction amount by currency
--
-- Refunds have negative amounts in the sample dataset. This query includes
-- purchases and refunds without combining currencies into one total.
-- ============================================================================

SELECT
    currency,
    COUNT_IF(event_type = 'purchase') AS purchase_count,
    COUNT_IF(event_type = 'refund') AS refund_count,
    SUM(TRY_CAST(amount AS DECIMAL(18, 2))) AS net_transaction_amount
FROM data_lake_events.events
WHERE event_type IN ('purchase', 'refund')
  AND event_date BETWEEN '2026-01-01' AND '2026-01-07'
GROUP BY currency
ORDER BY currency;


-- ============================================================================
-- 9. Find the highest-value purchase events
-- ============================================================================

SELECT
    event_id,
    event_timestamp,
    tenant_id,
    user_id,
    currency,
    TRY_CAST(amount AS DECIMAL(18, 2)) AS purchase_amount
FROM data_lake_events.events
WHERE event_type = 'purchase'
  AND event_date BETWEEN '2026-01-01' AND '2026-01-07'
ORDER BY purchase_amount DESC
LIMIT 10;


-- ============================================================================
-- 10. Calculate event counts per tenant
-- ============================================================================

SELECT
    tenant_id,
    COUNT(*) AS total_events,
    COUNT_IF(event_type = 'purchase') AS purchases,
    COUNT_IF(event_type = 'refund') AS refunds,
    COUNT_IF(event_type = 'page_view') AS page_views,
    COUNT_IF(event_type = 'signup') AS signups
FROM data_lake_events.events
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-07'
GROUP BY tenant_id
ORDER BY total_events DESC;


-- ============================================================================
-- 11. Identify duplicate event identifiers
--
-- A non-empty result indicates duplicate event IDs in the queried data.
-- ============================================================================

SELECT
    event_id,
    COUNT(*) AS occurrence_count
FROM data_lake_events.events
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-07'
GROUP BY event_id
HAVING COUNT(*) > 1
ORDER BY occurrence_count DESC;


-- ============================================================================
-- 12. Validate required fields
--
-- This query identifies records with missing or empty required values.
-- ============================================================================

SELECT
    event_id,
    event_date,
    tenant_id,
    event_type,
    user_id
FROM data_lake_events.events
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-07'
  AND (
      event_id IS NULL
      OR TRIM(event_id) = ''
      OR tenant_id IS NULL
      OR TRIM(tenant_id) = ''
      OR event_type IS NULL
      OR TRIM(event_type) = ''
      OR user_id IS NULL
      OR TRIM(user_id) = ''
  );


-- ============================================================================
-- 13. Validate numeric amount values
--
-- TRY_CAST returns NULL for invalid numeric strings instead of failing
-- the complete query.
-- ============================================================================

SELECT
    event_id,
    amount,
    currency,
    event_type
FROM data_lake_events.events
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-07'
  AND (
      amount IS NULL
      OR TRY_CAST(amount AS DECIMAL(18, 2)) IS NULL
  );


-- ============================================================================
-- 14. Inspect events with negative transaction amounts
-- ============================================================================

SELECT
    event_id,
    event_timestamp,
    tenant_id,
    event_type,
    amount,
    currency
FROM data_lake_events.events
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-07'
  AND TRY_CAST(amount AS DECIMAL(18, 2)) < 0
ORDER BY event_timestamp;


-- ============================================================================
-- 15. Inspect events for a specific tenant
-- ============================================================================

SELECT
    event_id,
    event_timestamp,
    event_type,
    amount,
    currency,
    source
FROM data_lake_events.events
WHERE tenant_id = 'tenant-001'
  AND event_date BETWEEN '2026-01-01' AND '2026-01-07'
ORDER BY event_timestamp;


-- ============================================================================
-- 16. Analyze page views by source and date
-- ============================================================================

SELECT
    event_date,
    source,
    COUNT(*) AS page_view_count,
    COUNT(DISTINCT user_id) AS unique_users
FROM data_lake_events.events
WHERE event_type = 'page_view'
  AND event_date BETWEEN '2026-01-01' AND '2026-01-07'
GROUP BY
    event_date,
    source
ORDER BY
    event_date,
    source;


-- ============================================================================
-- 17. Analyze signup activity
-- ============================================================================

SELECT
    event_date,
    source,
    currency,
    COUNT(*) AS signup_count,
    COUNT(DISTINCT tenant_id) AS tenant_count
FROM data_lake_events.events
WHERE event_type = 'signup'
  AND event_date BETWEEN '2026-01-01' AND '2026-01-07'
GROUP BY
    event_date,
    source,
    currency
ORDER BY
    event_date,
    source,
    currency;


-- ============================================================================
-- 18. Inspect JSON attributes
--
-- This example assumes attributes is available as MAP<STRING, STRING>.
-- Use element_at() for safe map lookup; absent keys return NULL.
-- ============================================================================

SELECT
    event_id,
    event_type,
    element_at(attributes, 'product_id') AS product_id,
    element_at(attributes, 'payment_method') AS payment_method
FROM data_lake_events.events
WHERE event_type = 'purchase'
  AND event_date BETWEEN '2026-01-01' AND '2026-01-07';


-- ============================================================================
-- 19. Find purchase events by payment method
-- ============================================================================

SELECT
    element_at(attributes, 'payment_method') AS payment_method,
    COUNT(*) AS purchase_count,
    SUM(TRY_CAST(amount AS DECIMAL(18, 2))) AS total_amount
FROM data_lake_events.events
WHERE event_type = 'purchase'
  AND event_date BETWEEN '2026-01-01' AND '2026-01-07'
GROUP BY element_at(attributes, 'payment_method')
ORDER BY purchase_count DESC;


-- ============================================================================
-- 20. Inspect storage partition coverage
--
-- This query reports partitions represented by records visible to Athena.
-- It does not independently prove that every expected S3 partition exists.
-- ============================================================================

SELECT
    event_date,
    COUNT(*) AS records_in_partition
FROM data_lake_events.events
GROUP BY event_date
ORDER BY event_date;


-- ============================================================================
-- 21. Inspect partition metadata registered in the Glue catalog
-- ============================================================================

SHOW PARTITIONS data_lake_events.events;


-- ============================================================================
-- 22. Query a single partition
--
-- Prefer partition predicates for routine analytics. They reduce the amount
-- of S3 data scanned when the table is correctly partitioned.
-- ============================================================================

SELECT
    event_type,
    COUNT(*) AS event_count,
    COUNT(DISTINCT tenant_id) AS tenant_count
FROM data_lake_events.events
WHERE event_date = '2026-01-07'
GROUP BY event_type
ORDER BY event_count DESC;


-- ============================================================================
-- 23. Calculate daily purchase and refund totals
-- ============================================================================

SELECT
    event_date,
    currency,
    SUM(
        CASE
            WHEN event_type = 'purchase'
                THEN TRY_CAST(amount AS DECIMAL(18, 2))
            ELSE CAST(0 AS DECIMAL(18, 2))
        END
    ) AS gross_purchases,
    SUM(
        CASE
            WHEN event_type = 'refund'
                THEN ABS(TRY_CAST(amount AS DECIMAL(18, 2)))
            ELSE CAST(0 AS DECIMAL(18, 2))
        END
    ) AS gross_refunds,
    SUM(TRY_CAST(amount AS DECIMAL(18, 2))) AS net_amount
FROM data_lake_events.events
WHERE event_type IN ('purchase', 'refund')
  AND event_date BETWEEN '2026-01-01' AND '2026-01-07'
GROUP BY
    event_date,
    currency
ORDER BY
    event_date,
    currency;


-- ============================================================================
-- 24. Detect unexpected event types
-- ============================================================================

SELECT
    event_type,
    COUNT(*) AS occurrence_count
FROM data_lake_events.events
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-07'
  AND event_type NOT IN (
      'purchase',
      'page_view',
      'refund',
      'signup'
  )
GROUP BY event_type
ORDER BY occurrence_count DESC;


-- ============================================================================
-- 25. Inspect timestamp parsing and UTC event dates
--
-- event_timestamp is stored as an ISO 8601 UTC string. from_iso8601_timestamp
-- parses the timestamp into a timestamp with time zone.
-- ============================================================================

SELECT
    event_id,
    event_timestamp,
    from_iso8601_timestamp(event_timestamp) AS parsed_timestamp,
    event_date
FROM data_lake_events.events
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-07'
ORDER BY event_timestamp;


-- ============================================================================
-- 26. Find records whose event_date differs from the UTC timestamp date
--
-- The sample contract defines event_date as the UTC calendar date.
-- ============================================================================

SELECT
    event_id,
    event_timestamp,
    event_date,
    CAST(
        from_iso8601_timestamp(event_timestamp) AT TIME ZONE 'UTC'
        AS DATE
    ) AS timestamp_utc_date
FROM data_lake_events.events
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-07'
  AND TRY_CAST(event_date AS DATE) <>
      CAST(
          from_iso8601_timestamp(event_timestamp) AT TIME ZONE 'UTC'
          AS DATE
      );


-- ============================================================================
-- 27. Inspect approximate data distribution by event type and date
--
-- Useful for validating ingestion volume and identifying unexpected
-- partition-level distribution changes.
-- ============================================================================

SELECT
    event_date,
    event_type,
    COUNT(*) AS event_count,
    COUNT(DISTINCT tenant_id) AS tenant_count,
    COUNT(DISTINCT user_id) AS user_count
FROM data_lake_events.events
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-07'
GROUP BY
    event_date,
    event_type
ORDER BY
    event_date,
    event_type;


-- ============================================================================
-- 28. Create an aggregated analytics table using CTAS
--
-- This creates a separate Parquet dataset. Replace the output S3 location
-- with a dedicated, private analytics prefix that is not the source prefix.
--
-- Run only when the target table does not already exist, or choose a new
-- target table name. CTAS writes data to S3 and can incur storage and query
-- charges.
-- ============================================================================

CREATE TABLE data_lake_events.daily_event_metrics
WITH (
    format = 'PARQUET',
    external_location = 's3://REPLACE_WITH_BUCKET_NAME/analytics/daily_event_metrics/',
    partitioned_by = ARRAY['event_date']
) AS
SELECT
    event_type,
    source,
    currency,
    COUNT(*) AS event_count,
    COUNT(DISTINCT tenant_id) AS tenant_count,
    COUNT(DISTINCT user_id) AS user_count,
    SUM(TRY_CAST(amount AS DECIMAL(18, 2))) AS total_amount,
    event_date
FROM data_lake_events.events
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-07'
GROUP BY
    event_type,
    source,
    currency,
    event_date;


-- ============================================================================
-- 29. Query the aggregated Parquet table
-- ============================================================================

SELECT
    event_date,
    event_type,
    source,
    currency,
    event_count,
    tenant_count,
    user_count,
    total_amount
FROM data_lake_events.daily_event_metrics
WHERE event_date BETWEEN '2026-01-01' AND '2026-01-07'
ORDER BY
    event_date,
    event_type,
    source,
    currency;


-- ============================================================================
-- 30. Remove the aggregated table from the Glue catalog
--
-- DROP TABLE removes the table metadata. For an external table, it does not
-- normally delete the underlying S3 objects. Verify the target location and
-- retention requirements before deleting any S3 data separately.
-- ============================================================================

-- DROP TABLE data_lake_events.daily_event_metrics;


-- ============================================================================
-- Production query guidelines
-- ============================================================================
--
-- 1. Always filter on event_date when querying bounded date ranges.
-- 2. Select only required columns instead of using SELECT *.
-- 3. Use TRY_CAST for potentially malformed numeric strings.
-- 4. Keep currency-specific monetary aggregates separate unless an explicit
--    exchange-rate conversion policy is applied.
-- 5. Avoid repeatedly scanning raw JSON for dashboards. Materialize
--    frequently used aggregates in Parquet or another suitable format.
-- 6. Use Athena workgroups to enforce query-result locations, encryption,
--    query limits, and cost controls.
-- 7. Monitor bytes scanned and execution time for recurring queries.
-- 8. Confirm partition registration or partition projection configuration.
-- 9. Do not assume that declaring a partition key in Glue automatically
--    registers S3 partitions.
-- 10. Keep Athena query results in a dedicated S3 location with appropriate
--     encryption, access controls, and lifecycle policies.
-- 11. Avoid placing query results under the raw ingestion prefix.
-- 12. Validate the Glue schema against the actual JSON representation.
--     In particular, the sample attributes contain mixed scalar values,
--     while the current table definition uses MAP<STRING, STRING>.
-- 13. CTAS output locations must be empty and must not overlap source data.
-- 14. Use separate workgroups or access controls for workloads with
--     different security, concurrency, and cost requirements.