# Django + gRPC Integration

A starter project demonstrating how a **Django** application's data layer can be exposed through a **gRPC service**. The gRPC server uses an `Employee` model defined in Django, showing how to separate HTTP and gRPC transport layers while sharing the same ORM.

---

## 📡 RPC Methods

| RPC Method    | Pattern    | Description                         |
|--------------|-----------|-------------------------------------|
| `GetEmployee`| **Unary** | Retrieve a single employee by ID    |

---

## 📁 Project Structure

```
05- Django-gRPC-Integration/
├── proto/
│   └── employee.proto               # Protobuf service & message definitions
├── grpc_service/
│   └── server.py                    # gRPC server (placeholder, ready for Django ORM)
├── django_project/
│   ├── manage.py                    # Django management script (placeholder)
│   ├── config/
│   │   └── settings.py              # Django settings
│   └── employees/
│       └── models.py                # Employee model (name, email)
├── requirements.txt                 # Python dependencies
├── run.md                           # Quick-run commands
├── .gitignore
└── README.md
```

---

## 🛠️ Prerequisites

- **Python 3.8+**
- **pip**
- **Django 5.2+**

---

## 🚀 Getting Started

### 1. Create & Activate a Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate Python Code from Proto

```bash
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/employee.proto
```

### 4. Set Up Django

```bash
cd django_project
python manage.py migrate
python manage.py runserver
```

### 5. Start the gRPC Server (in a separate terminal)

```bash
python grpc_service/server.py
```

The gRPC server starts on port `50051`.

---

## 📝 Protobuf Definition

Defined in [`proto/employee.proto`](proto/employee.proto):

```protobuf
syntax = "proto3";

package employee;

service EmployeeService {
  rpc GetEmployee (EmployeeRequest) returns (EmployeeResponse);
}

message EmployeeRequest {
  int32 id = 1;
}

message EmployeeResponse {
  int32 id = 1;
  string name = 2;
  string email = 3;
}
```

---

## 🔍 How It Works

```
                       ┌──────────────────────┐
                       │    Django ORM / DB    │
                       └──────────┬───────────┘
                                  │
                     Employee model (name, email)
                        ┌─────────┴─────────┐
                        │                   │
               ┌────────▼──────┐   ┌────────▼──────┐
               │  Django REST  │   │  gRPC Server  │
               │    :8000      │   │    :50051     │
               └───────────────┘   └───────────────┘
                     ▲                     ▲
                     │                     │
                HTTP/JSON              gRPC/Protobuf
                     │                     │
                 Browser              gRPC Client
```

### Key Integration Details

- **`grpc_service/server.py`** — Currently a placeholder that returns hardcoded demo data. In a production setup, this would call `django.setup()` and use `Employee.objects.get()` to query the Django ORM.
- **`django_project/employees/models.py`** — Defines the `Employee` model with `name` and `email` fields.
- The architecture separates the **Django HTTP transport** from the **gRPC transport**, while both share the same underlying data model.

### Extending This Starter

To connect the gRPC server to the Django ORM:

1. Add `django.setup()` to `grpc_service/server.py` before importing models.
2. Replace the hardcoded response with `Employee.objects.get(id=request.id)`.
3. Add more RPCs (e.g., `ListEmployees`, `CreateEmployee`) as needed.

---

## 📦 Dependencies

| Package        | Purpose                           |
|---------------|-----------------------------------|
| `grpcio`       | gRPC runtime                      |
| `grpcio-tools` | Protobuf compiler plugin for gRPC |
| `Django`       | Web framework & ORM               |

---

## 📄 License

This project is part of the [backend-engineering-playbook](../../../) and is intended for educational purposes.
