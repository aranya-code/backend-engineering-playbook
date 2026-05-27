# ENTRYPOINT vs CMD

## ENTRYPOINT

Defines the main executable that always runs.

---

## CMD

Provides default arguments for ENTRYPOINT.

---

## Example

```docker
ENTRYPOINT ["python"]
CMD ["app.py"]
```
