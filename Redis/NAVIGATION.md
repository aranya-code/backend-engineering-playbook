# Redis Playbook - Quick Navigation Index

> **Fast access to exactly what you need**

---

## 🎯 I Want To...

### Learn Redis from Scratch
→ Start here: [`concepts/01- Fundamentals/01- Introduction.md`](./concepts/01-%20Fundamentals/01-%20Introduction.md)  
→ Then: [`cli/01- Redis CLI Basics.md`](./cli/01-%20Redis%20CLI%20Basics.md)  
→ Practice: Install Redis and run commands

### Build a Project with Redis
→ FastAPI: [`sample projects/fastapi-redis-lab/`](./sample%20projects/fastapi-redis-lab/)  
→ Django: [`Django-FastAPI integration/01- Redis with Django.md`](./Django-FastAPI%20integration/01-%20Redis%20with%20Django.md)  
→ Patterns: [`caching/`](./caching/)

### Implement Caching
→ Fundamentals: [`caching/01- Caching Fundamentals.md`](./caching/01-%20Caching%20Fundamentals.md)  
→ Pattern: [`caching/02- Cache Aside Pattern.md`](./caching/02-%20Cache%20Aside%20Pattern.md)  
→ Problems: [`caching/08- Cache Stampede.md`](./caching/08-%20Cache%20Stampede.md)

### Deploy to Production
→ Guide: [`production/01- Production Deployment.md`](./production/01-%20Production%20Deployment.md)  
→ Scaling: [`production/02- Scaling Redis.md`](./production/02-%20Scaling%20Redis.md)  
→ Monitoring: [`production/04- Monitoring.md`](./production/04-%20Monitoring.md)

### Fix a Production Issue
→ Start: [`troubleshooting/14- Production Incident Playbook.md`](./troubleshooting/14-%20Production%20Incident%20Playbook.md)  
→ Common: [`troubleshooting/04- Memory Full.md`](./troubleshooting/04-%20Memory%20Full.md)  
→ Debug: [`troubleshooting/11- Performance Troubleshooting.md`](./troubleshooting/11-%20Performance%20Troubleshooting.md)

### Prepare for Interview
→ Questions: [`interview/01- Redis Interview Questions - Fundamentals.md`](./interview/01-%20Redis%20Interview%20Questions%20-%20Fundamentals.md)  
→ Cheatsheet: [`cheatsheets/05- Redis Interview Cheat Sheet.md`](./cheatsheets/05-%20Redis%20Interview%20Cheat%20Sheet.md)  
→ System Design: [`interview/09- Redis System Design Questions.md`](./interview/09-%20Redis%20System%20Design%20Questions.md)

---

## 📚 By Topic

### Architecture & Internals
- [Redis Architecture](./concepts/01-%20Fundamentals/02-%20Redis%20Architecture.md)
- [Persistence (RDB vs AOF)](./concepts/02-%20Data%20persistence/14-%20Persistence%20(RDB%20vs%20AOF).md)
- [Replication](./concepts/02-%20Data%20persistence/15-%20Replication.md)
- [Redis Sentinel](./concepts/03-%20Scaling/20-%20Redis%20Sentinel.md)
- [Redis Cluster](./concepts/03-%20Scaling/21-%20Redis%20Cluster.md)

### Data Structures
- [Strings](./concepts/01-%20Fundamentals/04-%20Strings.md) | [Commands](./cli/03-%20String%20Commands.md)
- [Lists](./concepts/01-%20Fundamentals/05-%20Lists.md) | [Commands](./cli/04-%20List%20Commands.md)
- [Sets](./concepts/01-%20Fundamentals/06-%20Sets.md) | [Commands](./cli/05-%20Set%20Commands.md)
- [Sorted Sets](./concepts/01-%20Fundamentals/07-%20Sorted%20Sets.md) | [Commands](./cli/06-%20Sorted%20Set%20Commands.md)
- [Hashes](./concepts/01-%20Fundamentals/08-%20Hashes.md) | [Commands](./cli/07-%20Hash%20Commands.md)
- [Streams](./concepts/01-%20Fundamentals/09-%20Streams.md) | [Commands](./cli/08-%20Stream%20Commands.md)

### Caching Patterns
- [Cache Aside](./caching/02-%20Cache%20Aside%20Pattern.md)
- [Read Through](./caching/03-%20Read%20Through%20Cache.md)
- [Write Through](./caching/04-%20Write%20Through%20Cache.md)
- [Write Behind](./caching/05-%20Write%20Behind%20Cache.md)
- [Refresh Ahead](./caching/06-%20Refresh%20Ahead%20Cache.md)
- [Eviction Strategies](./caching/07-%20Cache%20Eviction%20Strategies.md)

### Production Challenges
- [Cache Stampede](./caching/08-%20Cache%20Stampede.md)
- [Cache Avalanche](./caching/09-%20Cache%20Avalanche.md)
- [Cache Penetration](./caching/10-%20Cache%20Penetration.md)
- [Hot Keys](./caching/12-%20Hot%20Keys.md)
- [Rate Limiting](./caching/13-%20Rate%20Limiting.md)

### Framework Integration
- [Django Cache Framework](./Django-FastAPI%20integration/02-%20Django%20Cache%20Framework.md)
- [Django Sessions](./Django-FastAPI%20integration/03-%20Django%20Session%20Storage.md)
- [FastAPI Async](./Django-FastAPI%20integration/04-%20Redis%20with%20FastAPI.md)
- [Celery Integration](./Django-FastAPI%20integration/07-%20Celery%20with%20Redis.md)

---

## 🚀 By Experience Level

### Beginner
1. [Introduction](./concepts/01-%20Fundamentals/01-%20Introduction.md)
2. [Installing Redis](./concepts/01-%20Fundamentals/03-%20Installing%20Redis.md)
3. [Redis CLI Basics](./cli/01-%20Redis%20CLI%20Basics.md)
4. [Strings Tutorial](./concepts/01-%20Fundamentals/04-%20Strings.md)
5. [Basic Commands](./cli/03-%20String%20Commands.md)

### Intermediate
1. [All Data Structures](./concepts/01-%20Fundamentals/)
2. [Caching Patterns](./caching/)
3. [Framework Integration](./Django-FastAPI%20integration/)
4. [Sample Project](./sample%20projects/fastapi-redis-lab/)
5. [CLI Mastery](./cli/)

### Advanced
1. [Persistence](./concepts/02-%20Data%20persistence/)
2. [Scaling](./concepts/03-%20Scaling/)
3. [Production Deployment](./production/)
4. [Troubleshooting](./troubleshooting/)
5. [Performance Tuning](./production/05-%20Performance%20Tuning%20&%20Optimization.md)

---

## 💼 By Role

### Backend Engineer
**Primary Path**:
```
concepts/ → cli/ → caching/ → Django-FastAPI integration/ → sample projects/
```

**Key Files**:
- Architecture patterns in `caching/`
- Integration guides in `Django-FastAPI integration/`
- Working code in `sample projects/fastapi-redis-lab/`

### DevOps/SRE
**Primary Path**:
```
cli/ → production/ → troubleshooting/ → monitoring
```

**Key Files**:
- [Production Deployment](./production/01-%20Production%20Deployment.md)
- [Monitoring](./production/04-%20Monitoring.md)
- [Incident Playbook](./troubleshooting/14-%20Production%20Incident%20Playbook.md)
- [Performance Troubleshooting](./troubleshooting/11-%20Performance%20Troubleshooting.md)

### System Architect
**Primary Path**:
```
concepts/ → caching/ → production/ → system design
```

**Key Files**:
- [Redis Architecture](./concepts/01-%20Fundamentals/02-%20Redis%20Architecture.md)
- [Redis Cluster](./concepts/03-%20Scaling/21-%20Redis%20Cluster.md)
- [System Design Cheat Sheet](./cheatsheets/06-%20Redis%20System%20Design%20Cheat%20Sheet.md)
- [Scaling Redis](./production/02-%20Scaling%20Redis.md)

### Interview Candidate
**Primary Path**:
```
cheatsheets/ → interview/ → concepts/ → sample projects/
```

**Key Files**:
- [Interview Cheat Sheet](./cheatsheets/05-%20Redis%20Interview%20Cheat%20Sheet.md)
- [Fundamental Questions](./interview/01-%20Redis%20Interview%20Questions%20-%20Fundamentals.md)
- [System Design Questions](./interview/09-%20Redis%20System%20Design%20Questions.md)
- [Senior Backend Questions](./interview/10-%20Senior%20Backend%20Interview%20Questions.md)

---

## 🔥 Most Important Files

### Must-Read First (Top 10)
1. [`README.md`](./README.md) - Start here
2. [`concepts/01- Fundamentals/01- Introduction.md`](./concepts/01-%20Fundamentals/01-%20Introduction.md)
3. [`caching/01- Caching Fundamentals.md`](./caching/01-%20Caching%20Fundamentals.md)
4. [`caching/08- Cache Stampede.md`](./caching/08-%20Cache%20Stampede.md)
5. [`production/01- Production Deployment.md`](./production/01-%20Production%20Deployment.md)
6. [`troubleshooting/14- Production Incident Playbook.md`](./troubleshooting/14-%20Production%20Incident%20Playbook.md)
7. [`sample projects/fastapi-redis-lab/README.md`](./sample%20projects/fastapi-redis-lab/README.md)
8. [`interview/10- Senior Backend Interview Questions.md`](./interview/10-%20Senior%20Backend%20Interview%20Questions.md)
9. [`cheatsheets/05- Redis Interview Cheat Sheet.md`](./cheatsheets/05-%20Redis%20Interview%20Cheat%20Sheet.md)
10. [`cli/14- Redis CLI Cheat Sheet.md`](./cli/14-%20Redis%20CLI%20Cheat%20Sheet.md)

### Best Code Examples
1. [`sample projects/fastapi-redis-lab/`](./sample%20projects/fastapi-redis-lab/) - Complete FastAPI app
2. [`sample projects/fastapi-redis-lab/app/redis_client.py`](./sample%20projects/fastapi-redis-lab/app/redis_client.py) - Helper functions
3. [`sample projects/fastapi-redis-lab/app/services.py`](./sample%20projects/fastapi-redis-lab/app/services.py) - Service layer
4. [`sample projects/fastapi-redis-lab/REDIS_PATTERNS.md`](./sample%20projects/fastapi-redis-lab/REDIS_PATTERNS.md) - Pattern guide

---

## 📖 Common Scenarios

### "I need to add caching to my API"
1. Read: [`caching/01- Caching Fundamentals.md`](./caching/01-%20Caching%20Fundamentals.md)
2. Choose pattern: [`caching/02- Cache Aside Pattern.md`](./caching/02-%20Cache%20Aside%20Pattern.md)
3. Implementation:
   - Django: [`Django-FastAPI integration/02- Django Cache Framework.md`](./Django-FastAPI%20integration/02-%20Django%20Cache%20Framework.md)
   - FastAPI: [`sample projects/fastapi-redis-lab/`](./sample%20projects/fastapi-redis-lab/)
4. Avoid issues: [`caching/08- Cache Stampede.md`](./caching/08-%20Cache%20Stampede.md)

### "Redis is slow in production"
1. Diagnose: [`troubleshooting/11- Performance Troubleshooting.md`](./troubleshooting/11-%20Performance%20Troubleshooting.md)
2. Check: [`troubleshooting/05- High Latency.md`](./troubleshooting/05-%20High%20Latency.md)
3. Optimize: [`production/05- Performance Tuning & Optimization.md`](./production/05-%20Performance%20Tuning%20&%20Optimization.md)
4. Monitor: [`production/04- Monitoring.md`](./production/04-%20Monitoring.md)

### "I need to scale Redis"
1. Understand: [`concepts/03- Scaling/21- Redis Cluster.md`](./concepts/03-%20Scaling/21-%20Redis%20Cluster.md)
2. Deploy: [`production/02- Scaling Redis.md`](./production/02-%20Scaling%20Redis.md)
3. Sharding: [`concepts/03- Scaling/22- Sharding.md`](./concepts/03-%20Scaling/22-%20Sharding.md)
4. HA: [`production/03- High Availability.md`](./production/03-%20High%20Availability.md)

### "Redis crashed / won't start"
1. Quick fix: [`troubleshooting/01- Redis Won't Start.md`](./troubleshooting/01-%20Redis%20Won't%20Start.md)
2. Connection: [`troubleshooting/02- Connection Refused.md`](./troubleshooting/02-%20Connection%20Refused.md)
3. Memory: [`troubleshooting/04- Memory Full.md`](./troubleshooting/04-%20Memory%20Full.md)
4. Playbook: [`troubleshooting/14- Production Incident Playbook.md`](./troubleshooting/14-%20Production%20Incident%20Playbook.md)

### "Interview tomorrow"
**4-Hour Crash Course**:
1. Hour 1: [`cheatsheets/05- Redis Interview Cheat Sheet.md`](./cheatsheets/05-%20Redis%20Interview%20Cheat%20Sheet.md)
2. Hour 2: [`interview/01- Redis Interview Questions - Fundamentals.md`](./interview/01-%20Redis%20Interview%20Questions%20-%20Fundamentals.md)
3. Hour 3: [`interview/09- Redis System Design Questions.md`](./interview/09-%20Redis%20System%20Design%20Questions.md)
4. Hour 4: Review [`sample projects/fastapi-redis-lab/`](./sample%20projects/fastapi-redis-lab/) - be ready to explain

---

## 🎯 Learning Milestones

### Milestone 1: Redis Basics (Week 1)
- [ ] Installed Redis locally
- [ ] Executed 50+ CLI commands
- [ ] Understand 5 data structures
- [ ] Built simple cache-aside pattern
- [ ] Read `concepts/01- Fundamentals/`

### Milestone 2: Intermediate (Week 2-3)
- [ ] Implemented 3 caching patterns
- [ ] Integrated Redis with Django or FastAPI
- [ ] Understand persistence (RDB/AOF)
- [ ] Can debug with CLI tools
- [ ] Read `caching/` and `cli/`

### Milestone 3: Advanced (Week 4-6)
- [ ] Deployed Redis Cluster
- [ ] Handled production scenarios
- [ ] Built 2-3 Redis projects
- [ ] Understand replication and Sentinel
- [ ] Read `production/` and `troubleshooting/`

### Milestone 4: Expert (Ongoing)
- [ ] Can architect systems with Redis
- [ ] Contribute to production Redis
- [ ] Mentor others on Redis
- [ ] Pass senior interviews
- [ ] Completed entire repository

---

## 🗺️ Directory Map

```
Redis/
│
├── README.md ⭐ (Start here)
├── NAVIGATION.md (This file)
│
├── concepts/ 📚
│   ├── 01- Fundamentals/ (12 files)
│   ├── 02- Data persistence/ (7 files)
│   └── 03- Scaling/ (5 files)
│
├── cli/ 💻
│   └── (15 command guides)
│
├── caching/ ⚡
│   └── (14 pattern & problem docs)
│
├── Django-FastAPI integration/ 🐍
│   └── (11 integration guides)
│
├── production/ 🚀
│   └── (9 deployment & ops docs)
│
├── troubleshooting/ 🔧
│   └── (14 incident response guides)
│
├── interview/ 🎯
│   └── (12 interview prep docs)
│
├── cheatsheets/ 📋
│   └── (7 quick reference guides)
│
└── sample projects/ 💼
    ├── fastapi-redis-lab/ ⭐ (Complete app)
    └── django-redis-lab/ (Coming soon)
```

---

## ⚡ Quick Commands

### Find Specific Topics
```bash
# Search for caching patterns
find . -name "*Cache*.md"

# Find all CLI commands
ls cli/

# List all interview questions
ls interview/

# Browse sample code
cd "sample projects/fastapi-redis-lab"
```

### Start Learning Paths
```bash
# Beginner path
cd concepts/01-\ Fundamentals/
cat 01-\ Introduction.md

# Production path
cd production/
cat 01-\ Production\ Deployment.md

# Interview path
cd interview/
cat 01-\ Redis\ Interview\ Questions\ -\ Fundamentals.md

# Code path
cd "sample projects/fastapi-redis-lab"
cat README.md
```

---

## 🎓 Study Plans

### 1-Week Intensive
```
Mon: concepts/01- Fundamentals/ (4 hours)
Tue: cli/ + practice commands (4 hours)
Wed: caching/ patterns (4 hours)
Thu: Django-FastAPI integration/ (4 hours)
Fri: sample projects/fastapi-redis-lab/ (4 hours)
Sat: production/ + troubleshooting/ (4 hours)
Sun: interview/ + cheatsheets/ (4 hours)
```

### 1-Month Structured
```
Week 1: Fundamentals
  - concepts/01- Fundamentals/
  - cli/01-05
  - Build 2 simple projects

Week 2: Patterns & Integration
  - caching/
  - Django-FastAPI integration/
  - sample projects/fastapi-redis-lab/

Week 3: Advanced & Production
  - concepts/02-03
  - production/
  - Deploy Redis Cluster

Week 4: Mastery & Interview
  - troubleshooting/
  - interview/
  - cheatsheets/
  - Practice system design
```

### Self-Paced (Flexible)
```
Phase 1: Foundation (10-15 hours)
  concepts/01- Fundamentals/
  cli/01-07

Phase 2: Application (15-20 hours)
  caching/
  Django-FastAPI integration/
  Build projects

Phase 3: Production (10-15 hours)
  concepts/02-03
  production/
  troubleshooting/

Phase 4: Mastery (10+ hours)
  interview/
  cheatsheets/
  Advanced projects
```

---

## 📞 Need Help?

### Common Questions

**Q: Where do I start?**  
A: [`concepts/01- Fundamentals/01- Introduction.md`](./concepts/01-%20Fundamentals/01-%20Introduction.md)

**Q: I want working code examples**  
A: [`sample projects/fastapi-redis-lab/`](./sample%20projects/fastapi-redis-lab/)

**Q: How do I deploy to production?**  
A: [`production/01- Production Deployment.md`](./production/01-%20Production%20Deployment.md)

**Q: Redis is broken, help!**  
A: [`troubleshooting/14- Production Incident Playbook.md`](./troubleshooting/14-%20Production%20Incident%20Playbook.md)

**Q: Interview in 24 hours?**  
A: [`cheatsheets/05- Redis Interview Cheat Sheet.md`](./cheatsheets/05-%20Redis%20Interview%20Cheat%20Sheet.md)

---

## 🎯 Your Next Action

**Right Now, Go To**:

- **New to Redis?** → [`concepts/01- Fundamentals/01- Introduction.md`](./concepts/01-%20Fundamentals/01-%20Introduction.md)
- **Want to code?** → [`sample projects/fastapi-redis-lab/`](./sample%20projects/fastapi-redis-lab/)
- **Need caching?** → [`caching/02- Cache Aside Pattern.md`](./caching/02-%20Cache%20Aside%20Pattern.md)
- **Production issue?** → [`troubleshooting/14- Production Incident Playbook.md`](./troubleshooting/14-%20Production%20Incident%20Playbook.md)
- **Interview prep?** → [`interview/`](./interview/)

---

**Choose your path and start learning!** 🚀

*This navigation guide complements the main [README.md](./README.md)*
