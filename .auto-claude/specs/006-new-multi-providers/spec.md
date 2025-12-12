# Specification: New Multi Providers

> **CRITICAL: SPEC CRITIQUE FAILED**
>
> This spec has been flagged with critical issues by the Spec Critic Agent and **CANNOT proceed to implementation** in its current form.
>
> **Primary Issue**: Research/Spec Mismatch
> - The research.json contains information about graphiti-core library providers (for memory/embeddings)
> - The spec.md describes adding LLM providers to the Auto Claude AGENT framework
> - These are completely different features
>
> **Secondary Issue**: Technical Infeasibility
> - The spec assumes OpenAI and Gemini can replace claude_code_sdk
> - claude_code_sdk is an AGENT SDK with unique capabilities (MCP, hooks, sandboxing)
> - No equivalent SDKs exist for OpenAI/Gemini with these features
>
> **Action Required**: This spec needs to be either:
> 1. **Rewritten** with new research about agent SDK alternatives, OR
> 2. **Rescoped** to graphiti multi-provider support (matching the research)
>
> See `critique_report.json` for full analysis.

---

## Overview

This feature adds support for multiple LLM providers to the Auto Claude framework, enabling users to run autonomous coding agents with different AI models beyond Claude. Currently, the framework is tightly coupled to the Claude Code SDK via `client.py`. This enhancement will introduce a provider abstraction layer that supports Claude (existing), OpenAI, and other LLM providers, allowing users to choose their preferred model based on cost, performance, or availability requirements.

## Workflow Type

**Type**: feature

**Rationale**: This is a new capability that extends the framework's functionality by adding provider abstraction. It requires creating new modules, modifying existing components (`client.py`, `agent.py`, `run.py`), and potentially adding new dependencies. The scope involves architectural changes to decouple the existing Claude SDK integration and introduce a pluggable provider system.

## Task Scope

### Services Involved
- **auto-claude** (primary) - Core framework that orchestrates AI agent sessions
- **client.py** (refactor) - Currently creates Claude SDK client, will become provider factory
- **agent.py** (modification) - Agent session logic that uses the client

### This Task Will:
- [ ] Create a provider abstraction layer (`providers/base.py`) with common interface
- [ ] Implement Claude provider (`providers/claude.py`) wrapping existing SDK
- [ ] Implement OpenAI provider (`providers/openai.py`) for GPT-4/o1 models
- [ ] Implement Gemini provider (`providers/gemini.py`) for Google models
- [ ] Create provider factory (`providers/__init__.py`) for provider selection
- [ ] Add `--provider` CLI flag to `run.py` and `spec_runner.py`
- [ ] Add provider configuration via environment variables
- [ ] Update `client.py` to use provider abstraction
- [ ] Maintain backward compatibility with existing Claude-only workflows

### Out of Scope:
- Provider-specific MCP server integrations (keep existing behavior for Claude)
- Provider-specific security hooks beyond basic command allowlisting
- Cost tracking or budget management features
- Model fine-tuning or custom model support
- Streaming response handling differences (if not trivial)

## Service Context

### Auto Claude Framework

**Tech Stack:**
- Language: Python 3.8+
- Framework: Custom multi-agent framework
- Key directories: `auto-claude/`, `auto-claude/prompts/`, `auto-claude/specs/`

**Entry Point:** `auto-claude/run.py`

**How to Run:**
```bash
python auto-claude/run.py --spec 001
```

**Port:** N/A (CLI tool)

## Files to Modify

| File | Service | What to Change |
|------|---------|---------------|
| `auto-claude/client.py` | auto-claude | Refactor to use provider abstraction instead of direct Claude SDK |
| `auto-claude/run.py` | auto-claude | Add `--provider` CLI argument |
| `auto-claude/spec_runner.py` | auto-claude | Add `--provider` CLI argument |
| `auto-claude/agent.py` | auto-claude | Update client creation to pass provider parameter |
| `auto-claude/coordinator.py` | auto-claude | Update client creation for parallel workers |
| `auto-claude/qa_loop.py` | auto-claude | Update client creation for QA agents |
| `auto-claude/requirements.txt` | auto-claude | Add OpenAI and Google AI SDK dependencies |

## Files to Create

| File | Purpose |
|------|---------|
| `auto-claude/providers/__init__.py` | Provider factory and registry |
| `auto-claude/providers/base.py` | Abstract base class for providers |
| `auto-claude/providers/claude.py` | Claude provider implementation (wraps claude_code_sdk) |
| `auto-claude/providers/openai.py` | OpenAI provider implementation |
| `auto-claude/providers/gemini.py` | Google Gemini provider implementation |
| `auto-claude/providers/config.py` | Provider configuration and environment variable handling |

## Files to Reference

These files show patterns to follow:

| File | Pattern to Copy |
|------|----------------|
| `auto-claude/client.py` | Existing Claude SDK integration pattern |
| `auto-claude/graphiti_config.py` | Configuration pattern with environment variables |
| `auto-claude/linear_updater.py` | Optional feature enablement pattern |
| `auto-claude/security.py` | Hook pattern for provider-agnostic security |

## Patterns to Follow

### Configuration Pattern

From `auto-claude/graphiti_config.py`:

```python
@dataclass
class GraphitiConfig:
    enabled: bool = False
    host: str = "localhost"
    port: int = 6379

    @classmethod
    def from_env(cls) -> "GraphitiConfig":
        enabled = os.environ.get("GRAPHITI_ENABLED", "").lower() == "true"
        # ... load other config
        return cls(enabled=enabled, ...)
```

**Key Points:**
- Use dataclass for configuration
- Load from environment variables with sensible defaults
- Provide `from_env()` class method for easy initialization

### Optional Feature Pattern

From `auto-claude/linear_updater.py`:

```python
def is_linear_enabled() -> bool:
    """Check if Linear integration is enabled."""
    return bool(os.environ.get("LINEAR_API_KEY"))
```

**Key Points:**
- Simple function to check enablement
- Based on environment variable presence
- Used throughout codebase for conditional behavior

### Client Creation Pattern

From `auto-claude/client.py`:

```python
def create_client(project_dir: Path, spec_dir: Path, model: str) -> ClaudeSDKClient:
    """Create a Claude Agent SDK client with multi-layered security."""
    # Validate credentials
    # Configure security settings
    # Return configured client
```

**Key Points:**
- Accept project and spec directories for security context
- Accept model parameter for model selection
- Return configured client ready for use

## Requirements

### Functional Requirements

1. **Provider Abstraction**
   - Description: Create a common interface that all LLM providers implement
   - Acceptance: All providers implement `query()`, `receive_response()`, and context manager protocol

2. **Claude Provider (Default)**
   - Description: Wrap existing Claude Code SDK maintaining all current functionality
   - Acceptance: Running without `--provider` flag works exactly as before

3. **OpenAI Provider**
   - Description: Implement OpenAI provider using official Python SDK
   - Acceptance: Can run spec with `--provider openai` using GPT-4 models

4. **Gemini Provider**
   - Description: Implement Google Gemini provider using official SDK
   - Acceptance: Can run spec with `--provider gemini` using Gemini models

5. **Provider Selection**
   - Description: Allow provider selection via CLI flag and environment variable
   - Acceptance: `--provider openai` or `AUTO_BUILD_PROVIDER=openai` selects OpenAI

6. **Backward Compatibility**
   - Description: Existing workflows must continue working without changes
   - Acceptance: All existing tests pass, no changes needed to existing specs

### Non-Functional Requirements

1. **Error Handling**
   - Clear error messages when provider credentials are missing
   - Graceful fallback if provider unavailable

2. **Extensibility**
   - Easy to add new providers by implementing base interface
   - Provider registration pattern for discovery

### Edge Cases

1. **Missing Credentials** - Show clear error with setup instructions for each provider
2. **Invalid Provider Name** - List available providers and exit
3. **Provider Rate Limits** - Propagate rate limit errors with retry guidance
4. **Model Not Found** - Show available models for the selected provider

## Implementation Notes

### DO
- Follow the existing pattern in `graphiti_config.py` for configuration
- Keep Claude as the default provider for backward compatibility
- Use dependency injection pattern for provider selection
- Maintain existing security model (hooks, permissions) where applicable
- Document provider-specific environment variables in README.md

### DON'T
- Remove or break existing Claude SDK functionality
- Create provider-specific prompts (prompts should remain provider-agnostic)
- Add complex retry logic in the first version
- Make assumptions about provider-specific features (tool use, MCP, etc.)

## Development Environment

### Start Services

```bash
# Activate virtual environment
source auto-claude/.venv/bin/activate

# Run tests
pytest tests/ -v
```

### Required Environment Variables
- `CLAUDE_CODE_OAUTH_TOKEN`: Required for Claude provider (existing)
- `OPENAI_API_KEY`: Required for OpenAI provider (new)
- `GOOGLE_API_KEY`: Required for Gemini provider (new)
- `AUTO_BUILD_PROVIDER`: Optional, defaults to "claude"

## Success Criteria

The task is complete when:

1. [ ] Provider abstraction layer created with base interface
2. [ ] Claude provider implemented wrapping existing SDK
3. [ ] OpenAI provider implemented with GPT-4 support
4. [ ] Gemini provider implemented with Gemini Pro support
5. [ ] `--provider` flag added to run.py and spec_runner.py
6. [ ] Environment variable `AUTO_BUILD_PROVIDER` supported
7. [ ] Backward compatibility maintained (existing tests pass)
8. [ ] Provider selection documented in README.md
9. [ ] No console errors during normal operation
10. [ ] Existing tests still pass

## QA Acceptance Criteria

**CRITICAL**: These criteria must be verified by the QA Agent before sign-off.

### Unit Tests
| Test | File | What to Verify |
|------|------|----------------|
| Provider base interface | `tests/test_providers.py` | Abstract methods defined, cannot instantiate |
| Claude provider | `tests/test_providers.py` | Wraps SDK correctly, auth validation |
| OpenAI provider | `tests/test_providers.py` | API key validation, model selection |
| Gemini provider | `tests/test_providers.py` | API key validation, model selection |
| Provider factory | `tests/test_providers.py` | Returns correct provider by name |

### Integration Tests
| Test | Services | What to Verify |
|------|----------|----------------|
| Claude provider E2E | client.py <-> claude provider | Can create client and run simple query |
| Provider selection | run.py <-> provider factory | --provider flag routes to correct provider |

### End-to-End Tests
| Flow | Steps | Expected Outcome |
|------|-------|------------------|
| Default provider | 1. Run without --provider 2. Check client type | Uses Claude provider |
| OpenAI provider | 1. Set OPENAI_API_KEY 2. Run with --provider openai | Uses OpenAI provider |
| Invalid provider | 1. Run with --provider invalid | Shows error with available providers |

### Browser Verification (if frontend)
| Page/Component | URL | Checks |
|----------------|-----|--------|
| N/A | N/A | No frontend components |

### Database Verification (if applicable)
| Check | Query/Command | Expected |
|-------|---------------|----------|
| N/A | N/A | No database changes |

### QA Sign-off Requirements
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All E2E tests pass
- [ ] Browser verification complete (if applicable)
- [ ] Database state verified (if applicable)
- [ ] No regressions in existing functionality
- [ ] Code follows established patterns
- [ ] No security vulnerabilities introduced
- [ ] Documentation updated for new provider options
