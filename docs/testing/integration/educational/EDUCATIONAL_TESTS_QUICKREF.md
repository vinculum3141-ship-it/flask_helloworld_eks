# Educational Tests - Quick Reference

## 🎓 Three Educational Tests Added

### 1️⃣ Hostname-Based Routing
```bash
pytest test_k8s/test_service_ingress.py::test_hostname_routing_rejects_wrong_host -v -s
```
**Teaches:** Ingress routes on HTTP Host header, not URL  
**Shows:** Why `/etc/hosts` matters, why IP returns 404

### 2️⃣ Response Consistency  
```bash
pytest test_k8s/test_service_ingress.py::test_response_consistency_ingress_vs_direct -v -s
```
**Teaches:** Ingress is a transparent proxy  
**Shows:** Same response via Ingress vs direct access

### 3️⃣ Load Balancing
```bash
pytest test_k8s/test_service_ingress.py::test_ingress_load_balancing -v -s
```
**Teaches:** Load balancing at Service layer (not Ingress)  
**Shows:** Traffic distributed across pod replicas

---

## 🚀 Quick Commands

### Run all educational tests:
```bash
pytest test_k8s/ -m educational -v -s
```

### Run all Ingress tests (basic + educational):
```bash
pytest test_k8s/ -m ingress -v -s
```

### Exclude educational tests (run only basic validation):
```bash
pytest test_k8s/ -m "ingress and not educational" -v
```

---

## 📚 Documentation

**Full Guide:** [EDUCATIONAL_TESTS_GUIDE.md](EDUCATIONAL_TESTS_GUIDE.md)  
**Test README:** `test_k8s/README.md` (Educational Tests section)  
**Quick Reference:** This document

---

## 🎯 When to Use

| Scenario | Command |
|----------|---------|
| **Learning Ingress** | `pytest -m educational -v -s` |
| **Onboarding new team member** | `pytest -m educational -v -s` |
| **Quick validation (CI/CD)** | `pytest test_k8s/ -v` (default) |
| **Full test suite** | `pytest test_k8s/ -v -m ""` |
| **Troubleshooting routing** | Run Test 1 (hostname routing) |
| **Debugging responses** | Run Test 2 (consistency) |
| **Understanding traffic flow** | Run Test 3 (load balancing) |

---

## 💡 Key Learnings

### Test 1: Hostname Routing
```
✅ Host: hello-flask.local → 200 OK
❌ Host: wrong-hostname.local → 404 Not Found
❌ Host: 192.168.49.2 (IP) → 404 Not Found
```
**Takeaway:** Ingress is Layer 7 (HTTP), routes on Host header

### Test 2: Response Consistency
```
Ingress response == Direct response
```
**Takeaway:** Ingress doesn't modify application responses

### Test 3: Load Balancing
```
Request flow: Client → Ingress → Service → Pods (round-robin)
```
**Takeaway:** Service distributes traffic, not Ingress

---

## 📊 Test Execution Time

| Test | Duration |
|------|----------|
| Hostname Routing | ~5 seconds |
| Response Consistency | ~10 seconds |
| Load Balancing | ~30 seconds |
| **Total** | **~45 seconds** |

Basic Ingress tests: ~5 seconds  
Educational tests: ~45 seconds (run on-demand)

---

## ✨ Benefits

- 🎓 **Learning:** Understand how Ingress works internally
- 🔍 **Troubleshooting:** Know where to look when things fail
- 📖 **Documentation:** Tests demonstrate concepts, not just validate them
- 🚀 **Onboarding:** New team members learn by running tests
- 💪 **Confidence:** Deep understanding leads to better debugging

---

**Remember:** Use `-s` flag to see the educational output! 📝
