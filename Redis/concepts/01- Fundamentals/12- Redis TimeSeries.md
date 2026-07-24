# Redis TimeSeries

## Overview

RedisTimeSeries is an official Redis module designed for efficiently storing, querying, aggregating, and analyzing **time-series data**. Time-series data consists of measurements or events that are recorded over time, such as CPU utilization, stock prices, IoT sensor readings, application metrics, or website traffic.

While Redis Strings, Lists, or Sorted Sets can be used to store timestamped data, they require the application to handle aggregation, retention, downsampling, and querying manually. RedisTimeSeries provides these capabilities natively, making it significantly more efficient for monitoring and analytics workloads.

RedisTimeSeries is commonly used in observability platforms, monitoring systems, financial applications, IoT platforms, industrial automation, and machine learning pipelines.

---

# What is Time-Series Data?

Time-series data is any data where **time is the primary dimension**.

Examples include:

- CPU usage every second
- Website visitors every minute
- Temperature every hour
- Stock prices every millisecond
- API requests per minute

Conceptually:

```
Time

↓

10:00 → 25°C

10:01 → 26°C

10:02 → 24°C

10:03 → 27°C
```

Each measurement is associated with a timestamp.

---

# Why Use RedisTimeSeries?

Suppose an application stores CPU usage.

Without RedisTimeSeries:

```
Server

↓

CPU Usage

↓

Application

↓

Manual Storage

↓

Manual Aggregation

↓

Manual Cleanup
```

The application becomes responsible for:

- Managing timestamps
- Aggregating values
- Deleting old data
- Computing averages
- Calculating maximums

RedisTimeSeries performs these operations automatically.

---

# Internal Representation

Conceptually, RedisTimeSeries stores data as ordered timestamp-value pairs.

```
cpu:server-01

↓

Timestamp

↓

Value

↓

1721850000 → 65%

1721850060 → 72%

1721850120 → 68%

1721850180 → 74%
```

Redis automatically maintains the chronological order.

---

# Characteristics

RedisTimeSeries provides:

- Time-based storage
- Automatic ordering
- High compression
- Fast inserts
- Efficient queries
- Built-in aggregation
- Retention policies
- Label support
- Downsampling
- Continuous aggregation

These features significantly reduce application complexity.

---

# Time Complexity

| Operation | Complexity |
|------------|------------|
| Insert Sample | O(1) |
| Query by Time Range | O(log N + M) |
| Aggregation | Efficient |
| Retention Cleanup | Automatic |

RedisTimeSeries is optimized for high write throughput.

---

# Data Ingestion

New measurements are appended as they arrive.

```
Temperature Sensor

↓

RedisTimeSeries

↓

Timestamp

↓

Measurement
```

Since timestamps are automatically maintained, applications only submit new readings.

---

# Querying Historical Data

Applications frequently need historical information.

Example:

```
Show CPU Usage

↓

Last Hour
```

Redis retrieves only the requested time range.

Other examples:

- Last day
- Last week
- Previous month
- Custom date ranges

---

# Aggregation

Raw measurements often contain thousands of samples.

Instead of returning every value:

```
65

66

68

71

69

72

...
```

Redis can aggregate them.

Example:

```
Average

↓

68%
```

Supported aggregation functions include:

- Average
- Minimum
- Maximum
- Sum
- Count
- First
- Last

This reduces network traffic and simplifies reporting.

---

# Downsampling

High-frequency data can consume significant memory.

Example:

```
1 Reading

↓

Every Second
```

Instead of storing every measurement forever:

```
Every Second

↓

Average

↓

Every Minute
```

Applications retain meaningful historical information while reducing storage requirements.

---

# Retention Policies

Monitoring systems usually don't require old raw data indefinitely.

RedisTimeSeries supports automatic expiration.

```
Raw Data

↓

30 Days

↓

Automatically Removed
```

Applications no longer need scheduled cleanup jobs.

---

# Labels

Labels allow related time series to be grouped.

Example:

```
Server

↓

server-01

↓

Region

↓

Mumbai

↓

Environment

↓

Production
```

Applications can search metrics using these labels.

Example:

```
Region = Mumbai

↓

Return All Metrics
```

---

# Monitoring Applications

One of the most common production use cases.

```
Application

↓

CPU

Memory

Disk

Network

↓

RedisTimeSeries

↓

Dashboard
```

Metrics are continuously collected and visualized.

---

# DevOps and Observability

Modern infrastructure generates thousands of metrics.

```
Kubernetes Cluster

↓

Pods

↓

Containers

↓

Node Metrics

↓

RedisTimeSeries
```

Dashboards display historical performance trends.

---

# IoT Systems

Industrial devices continuously report measurements.

```
Sensor

↓

Temperature

Humidity

Pressure

Battery

↓

RedisTimeSeries
```

Millions of readings can be efficiently stored.

---

# Financial Applications

Financial systems process continuous market data.

Example:

```
Stock

↓

Timestamp

↓

Price
```

Applications can compute:

- Moving averages
- Highs
- Lows
- Volume trends

---

# AI and Machine Learning

Machine learning pipelines frequently consume time-series data.

Examples:

- Model performance
- GPU utilization
- Training metrics
- Prediction accuracy
- Feature drift

RedisTimeSeries enables fast retrieval for model monitoring.

---

# RedisTimeSeries vs Sorted Sets

| Feature | Sorted Set | RedisTimeSeries |
|----------|------------|-----------------|
| Timestamp Support | Manual | Native |
| Compression | No | Yes |
| Aggregation | Manual | Built-in |
| Retention | Manual | Automatic |
| Labels | No | Yes |

Sorted Sets can store timestamped data, but RedisTimeSeries provides significantly more functionality.

---

# RedisTimeSeries vs Relational Database

| Feature | SQL Database | RedisTimeSeries |
|----------|--------------|-----------------|
| Time-Series Optimized | No | Yes |
| Real-Time Inserts | Good | Excellent |
| Aggregation | SQL Queries | Built-in |
| Retention | Manual | Automatic |
| High Write Throughput | Moderate | Excellent |

SQL databases remain valuable for transactional data, while RedisTimeSeries excels at real-time metrics.

---

# Common Production Use Cases

RedisTimeSeries is widely used for:

- Infrastructure monitoring
- Application performance metrics
- DevOps dashboards
- IoT telemetry
- Industrial automation
- Financial market data
- Website analytics
- Business KPIs
- AI model monitoring
- Sensor data collection

---

# When Should You Use RedisTimeSeries?

Choose RedisTimeSeries when:

- Data is timestamp-based.
- Continuous measurements are collected.
- Historical analysis is required.
- Automatic aggregation is beneficial.
- Large volumes of metrics must be stored efficiently.

---

# When Should You Use Other Data Types?

| Requirement | Better Choice |
|-------------|---------------|
| User Profiles | Hashes |
| Cached Objects | Strings |
| Event Messaging | Streams |
| Rankings | Sorted Sets |
| Search | RediSearch |

Each Redis data structure is optimized for a specific class of problems.

---

# Production Considerations

When deploying RedisTimeSeries:

- Configure appropriate retention policies.
- Aggregate historical data to reduce storage costs.
- Monitor write throughput.
- Label metrics consistently.
- Separate production and development metrics.
- Archive long-term historical data if required.

---

# Best Practices

- Use meaningful metric names.
- Apply labels consistently across services.
- Retain raw data only as long as necessary.
- Downsample historical data.
- Monitor memory utilization.
- Combine RedisTimeSeries with Grafana or similar visualization tools for dashboards.

---

# RedisTimeSeries in Modern Architecture

A common production architecture:

```
Application

↓

Metrics Collector

↓

RedisTimeSeries

↓

Grafana Dashboard

↓

Alerts

↓

Operations Team
```

RedisTimeSeries serves as the high-speed storage layer, while visualization and alerting tools consume the aggregated metrics.

---

# Summary

RedisTimeSeries extends Redis with native support for time-series data, enabling efficient storage, querying, aggregation, and retention of timestamped measurements. It is purpose-built for monitoring, observability, IoT, financial analytics, and AI workloads where high write throughput and real-time analysis are essential. By handling aggregation, downsampling, and retention automatically, RedisTimeSeries significantly reduces application complexity and provides a scalable solution for modern metric-driven systems.

---

# Key Takeaways

- RedisTimeSeries is an official Redis module for time-series data.
- It stores timestamp-value pairs efficiently.
- Built-in aggregation eliminates complex application logic.
- Automatic retention policies simplify data lifecycle management.
- Labels enable grouping and filtering of related metrics.
- It is ideal for monitoring, IoT, DevOps, finance, and AI observability.
- RedisTimeSeries is far more efficient than using generic Redis data structures for time-series workloads.