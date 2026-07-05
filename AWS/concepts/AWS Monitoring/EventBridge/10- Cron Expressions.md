# Cron Expressions

Cron expressions define precise schedules for EventBridge Scheduler. They provide greater flexibility than rate expressions and allow tasks to run at specific times, dates, months, or days of the week.

------------------------------------------------------------------------

# What is a Cron Expression?

A cron expression specifies **when** a scheduled task should execute.

Example:

```text
cron(0 8 * * ? *)
```

Runs every day at **08:00 UTC**.

------------------------------------------------------------------------

# Cron Format

EventBridge uses six fields:

```text
cron(Minutes Hours Day-of-Month Month Day-of-Week Year)
```

Example:

```text
cron(30 9 * * ? *)
```

Runs every day at **09:30 UTC**.

------------------------------------------------------------------------

# Cron Fields

| Field | Values |
|--------|--------|
| Minutes | 0–59 |
| Hours | 0–23 |
| Day of Month | 1–31 |
| Month | 1–12 or JAN–DEC |
| Day of Week | 1–7 or SUN–SAT |
| Year | 1970–2199 |

------------------------------------------------------------------------

# Wildcards

Common wildcards include:

| Wildcard | Meaning |
|----------|---------|
| * | Every value |
| ? | No specific value |
| , | Multiple values |
| - | Range |
| / | Increment |

------------------------------------------------------------------------

# Common Examples

Every day at midnight:

```text
cron(0 0 * * ? *)
```

------------------------------------------------------------------------

Every weekday at 9 AM:

```text
cron(0 9 ? * MON-FRI *)
```

------------------------------------------------------------------------

Every Sunday at 6 PM:

```text
cron(0 18 ? * SUN *)
```

------------------------------------------------------------------------

First day of every month:

```text
cron(0 0 1 * ? *)
```

------------------------------------------------------------------------

Every 15 minutes:

```text
cron(0/15 * * * ? *)
```

------------------------------------------------------------------------

# Rate vs Cron

| Rate | Cron |
|------|------|
| Fixed intervals | Specific schedule |
| Easier to configure | More flexible |
| Minutes, Hours, Days | Full calendar scheduling |

------------------------------------------------------------------------

# Common Use Cases

- Nightly backups
- Monthly reports
- Weekly cleanup
- Payroll processing
- Certificate renewal
- Scheduled notifications

------------------------------------------------------------------------

# Common Mistakes

- Forgetting UTC timezone
- Invalid wildcard usage
- Incorrect day-of-month/day-of-week combinations
- Confusing cron with rate expressions

------------------------------------------------------------------------

# Best Practices

- Use cron for calendar-based schedules.
- Use rate for simple intervals.
- Test cron expressions.
- Document business schedules.
- Configure retries and DLQs.

------------------------------------------------------------------------

# Interview Questions

**Q. What is the difference between rate() and cron()?**

**Answer**

- `rate()` executes at fixed intervals.
- `cron()` executes according to a calendar schedule.

------------------------------------------------------------------------

# Key Takeaways

- Cron expressions provide flexible scheduling.
- EventBridge Scheduler uses six cron fields.
- Cron is ideal for business schedules.
- Rate expressions are better for simple recurring intervals.