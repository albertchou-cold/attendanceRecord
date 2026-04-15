# AI Extension Area

This folder is the reserved integration point for AI capabilities.

## Structure

- providers/: model vendor adapters (OpenAI, Anthropic, local)
- skills/: reusable domain skills
- service.py: provider selection and orchestration
- schemas.py: request/response contracts

## First production step

1. Install optional dependencies from requirements-ai.txt.
2. Set AI_PROVIDER=openai and OPENAI_API_KEY in .env.
3. Replace placeholder logic in providers/openai_provider.py with SDK call.
