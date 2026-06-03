# S3 Lifecycle Overview

## What is a Lifecycle Policy?

Lifecycle policies automatically manage objects throughout their lifecycle.

Instead of manually moving or deleting objects, AWS performs actions automatically.

## Why Use Lifecycle Policies?

- Reduce storage costs
- Automate data retention
- Simplify operations
- Meet compliance requirements

## Typical Flow

Day 0  -> S3 Standard
Day 30 -> Standard-IA
Day 90 -> Glacier
Day 365 -> Delete

## Benefits

- Automation
- Cost savings
- Consistent governance
