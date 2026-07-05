# CloudWatch Logs Insights

CloudWatch Logs Insights is an interactive log analytics service that allows you to search, analyze, and visualize log data stored in CloudWatch Logs. It uses a purpose-built query language to quickly troubleshoot production issues and identify trends.

---

# What is CloudWatch Logs Insights?

Logs Insights enables you to run queries against one or more CloudWatch Log Groups without exporting log data.

It is optimized for fast, ad hoc analysis of large volumes of logs.

---

# Why Use Logs Insights?

Logs Insights helps you:

- Troubleshoot production issues
- Search application logs
- Investigate errors
- Analyze API performance
- Identify trends
- Build visualizations

---

# How Logs Insights Works

```text
Applications / AWS Services
           |
           v
     CloudWatch Logs
           |
           v
     Logs Insights Query
           |
           +----------------+
           |                |
           v                v
      Search Results    Visual Charts
```

---

# Basic Query Structure

A query is composed of commands separated by the pipe (`|`) operator.

Example:

```text
fields @timestamp, @message
| sort @timestamp desc
| limit 20
```

---

# Common Query Commands

## fields

Selects which fields to display.

```text
fields @timestamp, @message
```

---

## filter

Filters matching log events.

```text
filter @message like /ERROR/
```

---

## sort

Sorts query results.

```text
sort @timestamp desc
```

---

## limit

Limits the number of returned records.

```text
limit 50
```

---

## stats

Aggregates data.

```text
stats count(*) by level
```

Useful for counting errors, requests, or events.

---

## parse

Extracts values from log messages.

```text
parse @message "* *" as level, message
```

Useful for unstructured application logs.

---

# Practical Query Examples

## Find Recent Errors

```text
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 20
```

---

## Count HTTP 500 Errors

```text
filter status = 500
| stats count(*) as Total500Errors
```

---

## Top API Endpoints

```text
stats count(*) by endpoint
| sort count desc
```

---

# Visualizing Results

Logs Insights can display query results as:

- Table
- Line chart
- Bar chart
- Stacked area chart

Visualizations help identify trends over time.

---

# Cost Considerations

Logs Insights pricing is based on the amount of log data scanned.

To reduce cost:

- Query only required Log Groups.
- Restrict the time range.
- Filter early in the query.
- Avoid scanning unnecessary logs.

---

# Real-World Example

A payment service begins returning intermittent failures.

An engineer runs:

```text
fields @timestamp, @message
| filter @message like /Payment/
| sort @timestamp desc
```

Within seconds, the query identifies repeated payment gateway timeout errors, allowing the team to resolve the issue quickly.

---

# Best Practices

- Use structured JSON logs whenever possible.
- Limit the query time window.
- Filter early to reduce scanned data.
- Save frequently used queries.
- Combine Logs Insights with Metric Filters and CloudWatch Alarms.

---

# Key Takeaways

- CloudWatch Logs Insights is an interactive log query service.
- It enables fast troubleshooting without exporting logs.
- Commands such as `fields`, `filter`, `stats`, `parse`, `sort`, and `limit` simplify log analysis.
- Efficient queries reduce both troubleshooting time and cost.
