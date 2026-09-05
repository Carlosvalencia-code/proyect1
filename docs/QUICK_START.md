# ⚡ Synthia Style - Quick Start Guide

**Get Synthia Style running in 30 seconds**

---

## 🚀 Development Setup (Ultra-Fast)

```bash
# 1. Clone and navigate
git clone <repository-url>
cd synthia-style-complete

# 2. One-command setup
make setup && make dev

# 3. Ready! 🎉
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000/docs
```

---

## 🌐 Production Deployment

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env and set:
# - GEMINI_API_KEY=your_api_key
# - POSTGRES_PASSWORD=secure_password
# - JWT_SECRET_KEY=secure_jwt_key

# 2. Deploy
make prod

# 3. Live! 🚀
# https://synthia.style
```

---

## 📋 Essential Commands

```bash
# Development
make dev              # Start development environment
make logs service=X   # View logs (backend, frontend, postgres, redis)
make health           # Check system health
make test             # Run tests

# Database
make db-studio        # Open Prisma Studio GUI
make db-shell         # PostgreSQL shell
make backup           # Create backup

# Production
make prod             # Deploy to production
make staging          # Deploy to staging
make monitor          # Start monitoring stack

# Utilities
make clean            # Clean up resources
make shell service=X  # Access container shell
make ps               # Show running services
```

---

## 🛠️ Development Tools

```bash
# Start development tools
make tools-up

# Available at:
# PgAdmin:        http://localhost:5050 (admin@synthia.style / admin_dev_2024)
# Redis Commander: http://localhost:8081 (admin / admin_dev_2024)
```

---

## 🔍 Troubleshooting

```bash
# Check service status
make status

# View all logs
make logs-all

# Health check with details
make health-detailed

# Reset development environment
make dev-clean && make dev
```

---

## 📊 URLs Reference

### Development
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PgAdmin**: http://localhost:5050
- **Redis Commander**: http://localhost:8081

### Production
- **Application**: https://synthia.style
- **API**: https://synthia.style/api/v1
- **API Docs**: https://synthia.style/api/v1/docs

---

## ⚙️ Environment Variables (Required)

```bash
# .env file (copy from .env.example)
GEMINI_API_KEY=your_gemini_api_key_here
POSTGRES_PASSWORD=secure_password_2024
REDIS_PASSWORD=secure_redis_password_2024
JWT_SECRET_KEY=secure_jwt_key_minimum_32_characters_2024
```

---

## 🆘 Need Help?

1. **Check Health**: `make health`
2. **View Logs**: `make logs service=backend`
3. **Reset Environment**: `make clean && make dev`
4. **Documentation**: See README.md for complete guide

---

**🎉 That's it! Synthia Style is production-ready with enterprise-grade containerization.**
