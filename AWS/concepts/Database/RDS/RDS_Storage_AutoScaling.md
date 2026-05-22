# RDS Storage Auto Scaling

## Purpose

Automatically increases DB storage when storage becomes low.

---

## Scaling Conditions

- Free storage < 10%
- Low storage lasts 5 minutes
- 6 hours since last scaling

---

## Important Note

Storage auto scaling only scales UP.

It does not automatically reduce storage.
