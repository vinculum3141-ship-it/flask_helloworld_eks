# Educational Tests Documentation

This directory contains documentation for educational Ingress tests that demonstrate Kubernetes concepts.

---

## 📚 Documentation

### Complete Guide
- **[EDUCATIONAL_TESTS_GUIDE.md](EDUCATIONAL_TESTS_GUIDE.md)** - Complete educational tests guide
  - Purpose and learning objectives
  - All three educational tests explained
  - How to run tests (local and CI/CD)
  - CI/CD integration and configuration
  - Expected output examples
  - Why these tests matter
  - Integration with documentation
  - How to extend with new educational tests

### Quick Reference
- **[EDUCATIONAL_TESTS_QUICKREF.md](EDUCATIONAL_TESTS_QUICKREF.md)** - Quick command reference
  - Common commands
  - Test execution examples
  - When to use each test
  - Key learnings summary

---

## 🎯 Purpose

**Standard tests answer:** "Does it work?"  
**Educational tests answer:** "How and why does it work?"

These tests are designed for:
- 📚 Learning Ingress concepts
- 🎓 Training team members
- 🔍 Demonstrating best practices
- 💡 Understanding troubleshooting techniques

---

## 🚀 Quick Start

### Run all educational tests:
```bash
pytest test_k8s/ -m educational -v -s
```

### Run specific test:
```bash
pytest test_k8s/test_service_ingress.py::test_hostname_routing_rejects_wrong_host -v -s
```

For more commands, see [EDUCATIONAL_TESTS_QUICKREF.md](EDUCATIONAL_TESTS_QUICKREF.md).

---

## 🔍 Quick Links

- [Back to Integration Tests](../)
- [Back to Testing Documentation](../../README.md)
- [Main Documentation](../../../README.md)
