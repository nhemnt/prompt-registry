# Prompt Registry

A production-ready Prompt Management & Observability API built with FastAPI and PostgreSQL.

### Database Setup & ORM Foundations
- [ ] Install PostgreSQL locally or via Docker
- [ ] Add SQLAlchemy + asyncpg
- [ ] Create DB session manager
- [ ] Create Base model class
- [ ] Add first model: Prompt
- [ ] Add UUID + timestamps fields
- [ ] Connect FastAPI to DB session
- [ ] Create test route to insert prompt
- [ ] Verify record in DB manually
- [ ] Add proper type hints everywhere

### Alembic Migrations
- [ ] Install Alembic
- [ ] Configure async migrations
- [ ] Generate first migration
- [ ] Apply migration locally
- [ ] Modify schema and create second migration
- [ ] Learn downgrade workflow
- [ ] Document migration commands in README
- [ ] Add migration check to CI (optional)

### Prompt Versioning System
- [ ] Create PromptVersion model
- [ ] Add FK relationship to Prompt
- [ ] Add JSON fields for variables/config
- [ ] Write service to create new version
- [ ] Implement “auto increment version”
- [ ] Add is_active logic
- [ ] Write route to create version
- [ ] Write route to fetch latest version
- [ ] Add DB index for active version
- [ ] Write unit test for version creation

### API Design & Validation
- [ ] Create Pydantic schemas for prompts
- [ ] Add request validation
- [ ] Add response models
- [ ] Implement list prompts endpoint
- [ ] Implement get prompt by name
- [ ] Add pagination support
- [ ] Add filtering by created date
- [ ] Add API error handling layer
- [ ] Add global exception middleware
- [ ] Document API responses properly

### Prompt Run Logging (Observability Core)
- [ ] Create PromptRun model
- [ ] Add JSON input storage
- [ ] Add latency + cost fields
- [ ] Write run logging service
- [ ] Add /runs endpoint
- [ ] Add background logging option
- [ ] Store timestamps automatically
- [ ] Write query for runs by prompt
- [ ] Add limit + sorting support
- [ ] Write test to simulate prompt execution logging

### Production Hardening
- [ ] Add API key auth middleware
- [ ] Add request logging
- [ ] Add error logging
- [ ] Add retry-safe DB transactions
- [ ] Add health check endpoint
- [ ] Add DB connectivity check endpoint
- [ ] Add structured JSON logs
- [ ] Add config for environments (dev/prod)
- [ ] Add startup validation checks
- [ ] Write deployment notes in README

### Performance & Scalability Basics
- [ ] Add Redis dependency
- [ ] Cache latest prompt version
- [ ] Invalidate cache on new version
- [ ] Add DB query optimization
- [ ] Add indexes where needed
- [ ] Measure latency before/after cache
- [ ] Document performance improvements

### Developer Experience & Tooling
- [ ] Add formatter (ruff/black)
- [ ] Add import sorting
- [ ] Add type checker (mypy optional)
- [ ] Add pre-commit hooks
- [ ] Add Makefile or scripts
- [ ] Add test runner config
- [ ] Add GitHub Actions CI
- [ ] Add coverage report
- [ ] Add local dev command shortcuts

### Final Polish & Portfolio Readiness
- [ ] Add architecture diagram
- [ ] Add API usage examples
- [ ] Add curl examples
- [ ] Add Dockerfile
- [ ] Add docker-compose for DB
- [ ] Add deployment guide
- [ ] Add project screenshots
- [ ] Write learning notes section
- [ ] Tag release v1.0
