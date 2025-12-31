# GLM-First Port 🚀

This is a complete port of Auto-Claude to prioritize **GLM-4** models as the primary AI provider, with 100x cost savings over traditional providers.

## 🎯 What Changed

### Core Architecture
- **Default AI Provider**: Changed from Claude to GLM across all services
- **Model Hierarchy**: GLM-4.7 (primary), GLM-4.6 (uncensored), GLM-4 (fast)
- **API Integration**: Native ZhipuAI SDK + Z.AI OpenAI-compatible endpoint
- **Cost Optimization**: ~$0.10 per 1M tokens vs $15-30 per 1M for Claude

### Backend Migration (25+ files)
All services, runners, and integrations now default to GLM:

#### **Runners** (`apps/backend/runners/`)
- ✅ `github_runner.py` - GitHub issue analysis with GLM
- ✅ `gitlab_runner.py` - GitLab MR review with GLM
- ✅ `roadmap_runner.py` - Roadmap generation with GLM
- ✅ `ideation_runner.py` - Feature ideation with GLM
- ✅ `spec_runner.py` - Spec generation with GLM
- ✅ `insights_runner.py` - Chat interface (GLM-4.7 & GLM-4.6 toggle)

#### **Services** (`apps/backend/services/`)
- ✅ `commit_message_service.py` - AI commit messages
- ✅ `workspace_merge_service.py` - Merge automation

#### **Integrations**
- ✅ `linear/updater.py` - Linear task sync with GLM
- ✅ `batch_analyzer.py` - Renamed to GLMBatchAnalyzer

#### **Merge AI Resolver** (`apps/backend/merge/ai_resolver/`)
- ✅ `glm_client.py` - NEW: Native GLM conflict resolution
- ✅ `__init__.py` - Auto-selects GLM/Claude based on AI_PROVIDER env var

### Frontend Migration (30+ files)

#### **Model Configuration** (`apps/frontend/src/shared/constants/models.ts`)
- ✅ `AVAILABLE_MODELS` - GLM-4.7 and GLM-4.6 listed first
- ✅ Legacy Claude models labeled "(Legacy)"
- ✅ `DEFAULT_AGENT_PROFILES` - GLM-4.7 is default profile
- ✅ `DEFAULT_PHASE_MODELS` - All phases use GLM-4.7
- ✅ `DEFAULT_FEATURE_MODELS` - All features use GLM-4.7

#### **User-Facing Labels Updated**
All "Claude" references changed to "AI" or "GLM":
- Authentication sections: "AI Authentication" / "GLM API"
- Settings labels: "AI Accounts", "AI Auth"
- Modal titles: "AI API Key Required", "GLM API Key Required"
- Terminal titles: "GLM" instead of "Claude"
- Usage indicators: "AI usage status"
- Rate limit modals: "AI Operation"

#### **i18n Translations** (English & French)
- ✅ `en/settings.json` - All labels updated to AI/GLM
- ✅ `fr/settings.json` - All labels updated to IA/GLM
- Legacy CLI path labels for backwards compatibility

#### **Components Updated**
- `Terminal.tsx`, `SDKRateLimitModal.tsx`, `UsageIndicator.tsx`
- `ClaudeAuthSection.tsx`, `ClaudeOAuthFlow.tsx`, `EnvironmentSettings.tsx`
- `SectionRouter.tsx`, `OAuthStep.tsx`, `IntegrationSettings.tsx`
- `EnvConfigModal.tsx`, `Ideation.tsx`, and more...

### Rate Limiter
- ✅ Added GLM pricing tiers (glm-4, glm-4-plus, glm-4-air, etc.)
- ✅ Updated cost calculations for GLM models

## 🔧 Configuration

### Environment Variables
```bash
# Required for GLM
AI_PROVIDER=glm
ZHIPUAI_API_KEY=your-api-key-here

# Optional: GLM-specific settings
GLM_BASE_URL=https://api.z.ai/api/coding/paas/v4  # OpenAI-compatible endpoint
DEFAULT_MODEL=glm-4.7  # Primary model
FALLBACK_MODEL=glm-4   # Fast fallback
```

### API Key Setup
1. Get API key from [Z.AI](https://api.z.ai) or [ZhipuAI](https://open.bigmodel.cn)
2. Add to `.env` or configure in app settings
3. Start using GLM-powered features

## 📊 Cost Comparison

| Provider | Model | Input | Output | 1M Tokens |
|----------|-------|-------|--------|-----------|
| **GLM** | glm-4.7 | $0.05 | $0.05 | **$0.10** |
| Claude | opus | $15 | $75 | **$15-75** |
| Claude | sonnet | $3 | $15 | **$3-15** |
| OpenAI | GPT-4 | $10 | $30 | **$10-30** |

**Savings: 100-750x cheaper than Claude Opus** 💰

## 🎨 Features Preserved

All original Auto-Claude features work with GLM:
- ✅ Autonomous task execution
- ✅ Multi-phase builds (spec, planning, coding, QA)
- ✅ Parallel execution (up to 12 terminals)
- ✅ Isolated git worktrees
- ✅ Self-validating QA loops
- ✅ AI-powered merge resolution
- ✅ Memory layer integration
- ✅ GitHub/GitLab/Linear integrations
- ✅ Roadmap & ideation generation
- ✅ Insights chat (with GLM-4.6 uncensored toggle)

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install zhipuai
   ```

2. **Configure Environment**
   ```bash
   echo "AI_PROVIDER=glm" >> apps/backend/.env
   echo "ZHIPUAI_API_KEY=your-key" >> apps/backend/.env
   ```

3. **Run the App**
   ```bash
   npm run dev
   ```

4. **Use GLM in UI**
   - Select "GLM-4.7 (Default)" profile in agent settings
   - Or use "GLM-4.6" for uncensored narrative mode
   - Legacy Claude profiles still available if needed

## 🔍 Technical Details

### Insights Chat
Two GLM modes available:
- **GLM-4.7**: Full tool support via GLMAgentClient (OpenAI-compatible)
- **GLM-4.6**: Direct ZhipuAI SDK with `eni_prompt` for uncensored responses

### Merge Conflict Resolution
Native GLM resolver in `apps/backend/merge/ai_resolver/glm_client.py`:
- Uses ZhipuAI SDK directly
- Temperature 0.3 for precise code merging
- Uncensored mode via `eni_prompt` system message

### Model Selection
Auto-selection based on `AI_PROVIDER` environment variable:
```python
from apps.backend.merge.ai_resolver import create_ai_resolver

resolver = create_ai_resolver()  # Auto-selects GLM if AI_PROVIDER=glm
```

## 📝 Backwards Compatibility

Legacy Claude functionality preserved:
- Claude profiles still available (labeled "Legacy")
- Claude API keys still configurable
- Switch back via `AI_PROVIDER=claude` in .env
- Frontend gracefully handles both providers

## 🌟 Why GLM?

1. **Cost**: 100x cheaper than Claude Opus
2. **Speed**: Comparable or faster response times
3. **Quality**: Excellent for coding tasks
4. **Uncensored**: GLM-4.6 mode for unrestricted responses
5. **Chinese Support**: Native Chinese language model
6. **Local Alternative**: Can run locally if needed

## 📚 Documentation

- [GLM Quick Start](./GLM_QUICKSTART.md) - Original GLM setup guide
- [Insights Configuration](./docs/INSIGHTS_GLM47_CONFIG.md) - GLM-4.7 config details
- [Insights Quick Reference](./docs/INSIGHTS_GLM47_QUICKREF.md) - Model parameters

## 🤝 Contributing

This fork maintains compatibility with the original Auto-Claude while prioritizing GLM as the default provider. Pull requests welcome for:
- Additional GLM model support
- Performance optimizations
- Cost tracking improvements
- Documentation enhancements

## 📄 License

Same as original Auto-Claude: AGPL-3.0

---

**Ready to fork?** This is a complete, production-ready GLM port with all features working. 🚀
