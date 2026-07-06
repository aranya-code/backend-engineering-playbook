# 🧭 Backend Engineering Playbook

A structured, hands-on knowledge base for backend engineering — built one technology at a time, with concept notes, CLI references, and real troubleshooting write-ups from actual practice.

---

## 📚 Topics

| Topic | Covers |
|-------|--------|
| [Docker](Docker/) | Container fundamentals through Compose, Swarm, and production-ready Dockerfiles |
| [Kubernetes](Kubernetes/) | Core objects, networking, storage, Helm, and cluster orchestration |
| [AWS](AWS/) | Compute, storage, IAM, networking, messaging, and monitoring across core services |
| [Nginx](Nginx/) | Reverse proxy and load balancing fundamentals |



---

## 🗂️ How Topics Are Organized

Every topic has a `concepts/` folder for theory notes, and most also include:

| Folder | Contains |
|--------|----------|
| `cli/` | Quick-reference command sheets |
| `troubleshooting/` | Real problems hit during hands-on practice, with root cause and fix |
| `images/` | Supporting screenshots and diagrams |

Each topic — and most of its subfolders — has its own `README.md` indexing what's inside, so you can drill down from here to any specific note. A few gaps while things fill in: Nginx doesn't have a `cli/` folder yet, and Kubernetes doesn't have `troubleshooting/` or `images/` folders yet (it has a `sample files/` folder with example manifests instead).

---

## 🎯 Purpose

This repository exists to:

- Consolidate learning into searchable, structured notes rather than scattered files
- Prepare for backend engineering interviews — concept explanations and interview Q&A are built into most topics
- Document real issues hit during hands-on practice, not just textbook theory

New topics — Django, FastAPI, SQL, and whatever comes after — will follow the same pattern above as they're added. This page just needs a new table row, not a rewrite.

---

*Aranya Majumdar — [github.com/aranya-code](https://github.com/aranya-code)*