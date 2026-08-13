# Namespaces

CloudWatch organizes metrics into logical containers called **Namespaces**. A namespace acts as a top-level grouping that separates metrics belonging to different AWS services or custom applications.

Namespaces help prevent naming conflicts and make metrics easier to organize, search, and manage.

---

# What is a Namespace?

A namespace is a container for related CloudWatch metrics.

Every metric belongs to exactly one namespace.

For example, the metric **CPUUtilization** exists under the **AWS/EC2** namespace.

```text
Namespace : AWS/EC2
Metric    : CPUUtilization
```

---

# Why are Namespaces Important?

Namespaces help you:

- Organize metrics logically
- Separate AWS metrics from custom metrics
- Avoid metric name conflicts
- Simplify monitoring and dashboards
- Improve metric filtering

---

# AWS Default Namespaces

AWS services automatically publish metrics to predefined namespaces.

| Service | Namespace |
|---------|-----------|
| Amazon EC2 | AWS/EC2 |
| AWS Lambda | AWS/Lambda |
| Amazon RDS | AWS/RDS |
| Amazon S3 | AWS/S3 |
| Amazon DynamoDB | AWS/DynamoDB |
| Elastic Load Balancer | AWS/ApplicationELB |
| Amazon ECS | AWS/ECS |
| Amazon SNS | AWS/SNS |
| Amazon SQS | AWS/SQS |

You cannot change AWS-managed namespaces.

---

# Custom Namespaces

Applications can publish metrics to custom namespaces.

Examples:

- MyApplication
- Ecommerce
- Payments
- Inventory
- Analytics

Choose names that clearly represent the application or business domain.

---

# Namespace Hierarchy

```text
AWS/EC2
   ├── CPUUtilization
   ├── NetworkIn
   ├── NetworkOut
   └── StatusCheckFailed

MyApplication
   ├── ActiveUsers
   ├── OrdersProcessed
   └── CheckoutLatency
```

---

# Naming Best Practices

- Use meaningful names.
- Keep naming consistent.
- Group related metrics together.
- Avoid generic names such as `Test` or `App`.
- Separate environments if appropriate, for example:
  - MyApp/Production
  - MyApp/Staging
  - MyApp/Development

---

# Namespaces vs Dimensions

Namespaces organize groups of metrics, while dimensions identify individual resources within a metric.

Example:

```text
Namespace : AWS/EC2
Metric    : CPUUtilization
Dimension : InstanceId=i-0123456789abcdef0
```

Use namespaces for grouping and dimensions for filtering.

---

# Real-World Example

An e-commerce platform uses:

- Ecommerce/Orders
- Ecommerce/Payments
- Ecommerce/Inventory

Each namespace contains metrics relevant to that business domain, making dashboards and alarms easier to maintain.

---

# Best Practices

- Reuse namespaces across related applications.
- Use descriptive names instead of abbreviations.
- Keep a consistent naming convention across teams.
- Do not mix unrelated metrics in the same namespace.
- Document namespace standards for your organization.

---

# Key Takeaways

- A namespace is a logical container for CloudWatch metrics.
- AWS services publish metrics to predefined namespaces.
- Custom applications can publish metrics to custom namespaces.
- Good namespace design improves monitoring, dashboards, and troubleshooting.
