# Project Refactor Guide (Industry Style)

## Current Architecture

- app/config.py: centralized typed settings
- app/main.py: FastAPI app with lifespan startup/shutdown
- app/database.py: HR/MES engine factories
- app/api/v1/endpoints/\*: HTTP API layer
- app/services/\*: business logic layer
- app/workers/\*: async/background jobs and schedulers
- app/ai/\*: reserved AI extension area

## Startup/Shutdown Contract

1. create_db_and_tables()
2. conditional workers by env:
   - PRODUCT_ADD_SCHEDULER_ENABLED
   - REWARM_SCHEDULER_ENABLED
   - REDIS_LISTENER_ENABLED
3. graceful stop on shutdown:
   - stop_product_add_scheduler()
   - stop_rewarm_scheduler()
   - stop_redis_listener()

## AI Integration Contract

- Provider abstraction: app/ai/providers/base.py
- Provider selection: app/ai/service.py
- Skills entry: app/ai/skills/\*
- API namespace: /api/v1/ai/\*

## Optional AI Dependencies

- Install with: pip install -r requirements-ai.txt

## Suggested Next Refactor Steps

1. Create tests/ with pytest and at least smoke tests for:
   - /api/v1/health
   - /api/v1/product-add/run (dry_run)
   - /api/v1/ai/health
2. Migrate deprecated files into a dedicated legacy folder or remove them.
3. Add global exception handlers and structured logging.
4. Add authentication/authorization for mutation endpoints.
5. Replace placeholder OpenAI provider with real SDK integration.
