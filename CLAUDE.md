# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ATS (Automated Testing System) is an enterprise-grade test management platform with a FastAPI backend and Vue 3 frontend. The system manages test cases, test plans, executions, and reporting with role-based access control.

## Essential Commands

### Backend Development
```bash
# Install dependencies (requires uv: curl -LsSf https://astral.sh/uv/install.sh | sh)
cd backend
make install          # Install production dependencies
make dev              # Install with dev dependencies

# Start services
docker-compose up -d   # Start MySQL, Redis, RabbitMQ, MinIO

# Database setup
make migrate          # Run migrations
make migrate-create message="your migration"  # Create new migration

# Development
make run              # Start FastAPI server (port 8000, auto-reload)
make celery          # Start Celery worker for async tasks

# Testing & Quality
make test            # Run pytest suite
make lint            # Run flake8 and mypy
make format          # Format with black and isort
```

### Frontend Development
```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start dev server (port 3000)
npm run build        # Production build
npm run lint         # ESLint with auto-fix
npm run type-check   # TypeScript checking
```

### API Documentation
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## Architecture Overview

### Backend Structure
- **FastAPI** application with async support
- **SQLAlchemy** ORM with MySQL 8.0 database
- **JWT authentication** with access (60min) and refresh (30d) tokens
- **RBAC permissions** system with project-level overrides
- **Celery** for async tasks (import/export operations)
- **8 API routers** in `/backend/api/v1/`: projects, test_cases, test_plans, environments, dashboard, executions, users, auth

### Frontend Structure
- **Vue 3** with Composition API and TypeScript
- **Ant Design Vue** component library
- **Pinia** for state management (user and project stores)
- **Axios** with interceptors for API calls and automatic token refresh
- **Vite** build tool with proxy configuration for `/api` routes

### Key Models & Relationships
- **User/Role/Permission**: RBAC with many-to-many relationships
- **Project/ProjectMember**: Team collaboration with project-specific roles
- **TestCase/Module**: Hierarchical test organization with parent-child modules
- **TestPlan/PlanCaseRelation**: Test planning with case selection and ordering
- **TestExecution**: Test run results (passed/failed/blocked/skipped)
- **Environment**: Test environment configurations stored as JSON

### API Response Format
All endpoints return standardized responses:
```json
{
  "status": "success|error|warning",
  "message": "Human-readable message",
  "data": {},
  "code": 200,
  "timestamp": "ISO-8601",
  "request_id": "tracking-id"
}
```

## Development Patterns

### Backend Patterns
- **Dependency injection** via FastAPI's `Depends()` for database sessions and current user
- **Service layer** pattern: Business logic in `/backend/services/`, not in routers
- **Pydantic schemas** for request/response validation in `/backend/schemas/`
- **Base model** with UUID primary keys and automatic timestamps
- **Cascade deletes** configured in SQLAlchemy relationships

### Frontend Patterns
- **API clients** in `/frontend/src/api/` with consistent error handling
- **Route guards** for authentication in `/frontend/src/router/`
- **Composables** for shared logic using Vue Composition API
- **Type definitions** in `/frontend/src/types/` for TypeScript support
- **Lazy loading** for routes with dynamic imports

### Authentication Flow
1. Login via `/api/v1/auth/login` returns access and refresh tokens
2. Access token sent as `Authorization: Bearer <token>` header
3. On 401, automatic refresh attempt using refresh token
4. Failed refresh redirects to login page

### Permission System
- Format: `resource:action` (e.g., "test_case:create")
- 22 system permissions defined in `/backend/core/permissions.py`
- Check via `has_permission()` in routers with `current_user` dependency
- Project-level overrides via `ProjectPermission` model

## Testing Strategy

### Running Tests
```bash
# Backend: Run all tests with coverage
cd backend && make test

# Frontend: Run Vitest tests
cd frontend && npm run test
```

### Test Organization
- Backend tests in `/backend/tests/` following source structure
- Use `pytest-asyncio` for async endpoint testing
- Mock database sessions and external services
- Minimum 80% coverage requirement

## Common Tasks

### Adding a New API Endpoint
1. Define Pydantic schemas in `/backend/schemas/`
2. Create service functions in `/backend/services/`
3. Add router endpoint in `/backend/api/v1/`
4. Add frontend API client in `/frontend/src/api/`
5. Update TypeScript types in `/frontend/src/types/`

### Creating Database Migration
```bash
cd backend
make migrate-create message="add_new_column_to_users"
# Review generated migration in /backend/alembic/versions/
make migrate  # Apply migration
```

### Debugging Database Queries
Enable SQL echo in `/backend/database.py` by setting `echo=True` in development mode.

### Working with Celery Tasks
1. Define task in `/backend/tasks/`
2. Start worker: `make celery`
3. Monitor via RabbitMQ management UI: http://localhost:15672

## Environment Configuration

### Backend Environment Variables
Key settings in `/backend/config.py`:
- `DATABASE_URL`: MySQL connection string
- `JWT_SECRET_KEY`: Must change in production
- `REDIS_URL`: Cache and session storage
- `RABBITMQ_URL`: Async task queue
- `MINIO_ENDPOINT`: File storage service

### Frontend Proxy Configuration
Development proxy in `/frontend/vite.config.ts` forwards:
- `/api` → `http://localhost:8000`
- `/ws` → `ws://localhost:8000`

## Current Status

Modified files awaiting commit:
- `backend/api/v1/test_cases.py`
- `backend/main.py`
- `backend/schemas/test_case.py`
- `frontend/src/components/TestCase/TestCaseEdit.vue`

Recent features:
- Test plan and project management module updates
- Refactored project management page with optimized routing