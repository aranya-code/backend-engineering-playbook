# Shell Form vs Exec Form

# Shell Form

```docker
CMD python app.py
```

Runs through:

```bash
/bin/sh -c
```

---

# Exec Form

```docker
CMD ["python", "app.py"]
```

Runs directly without shell.
