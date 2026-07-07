# Database Normalization

# Introduction

Normalization organizes relational data to reduce redundancy and improve data integrity.

---

# Goals

- Eliminate duplicate data
- Improve consistency
- Simplify maintenance

---

# Normal Forms

## First Normal Form (1NF)

- Atomic values
- No repeating groups

## Second Normal Form (2NF)

- Meets 1NF
- No partial dependency on composite keys

## Third Normal Form (3NF)

- Meets 2NF
- No transitive dependency

---

# Advantages

- Reduced duplication
- Easier updates
- Better integrity

---

# Disadvantages

- More JOIN operations
- Can impact read performance

---

# Best Practices

Normalize OLTP databases, then selectively denormalize for performance if necessary.

---

# Interview Questions

1. Why normalize a database?
2. Explain 1NF, 2NF, and 3NF.
3. When can normalization hurt performance?

---

# Quick Revision

Normalization reduces redundancy and improves integrity.
