/**
 * Model and agent profile constants
 * Claude models, thinking levels, memory backends, and agent profiles
 */

import type { AgentProfile, PhaseModelConfig, FeatureModelConfig, FeatureThinkingConfig } from '../types/settings';

// ============================================
// Available Models
// ============================================

export const AVAILABLE_MODELS = [
  { value: 'glm-4-7', label: 'GLM-4.7' },
  { value: 'glm-4-6', label: 'GLM-4.6' },
  { value: 'opus', label: 'Opus (Legacy)' },
  { value: 'sonnet', label: 'Sonnet (Legacy)' },
  { value: 'haiku', label: 'Haiku (Legacy)' }
] as const;

// Maps model shorthand to actual model IDs (Claude and GLM)
export const MODEL_ID_MAP: Record<string, string> = {
  opus: 'claude-opus-4-5-20251101',
  sonnet: 'claude-sonnet-4-5-20250929',
  haiku: 'claude-haiku-4-5-20251001',
  'glm-4-7': 'glm-4.7',
  'glm-4-6': 'glm-4.6'
} as const;

// Maps thinking levels to budget tokens (null = no extended thinking)
export const THINKING_BUDGET_MAP: Record<string, number | null> = {
  none: null,
  low: 1024,
  medium: 4096,
  high: 16384,
  ultrathink: 65536
} as const;

// ============================================
// Thinking Levels
// ============================================

// Thinking levels for Claude model (budget token allocation)
export const THINKING_LEVELS = [
  { value: 'none', label: 'None', description: 'No extended thinking' },
  { value: 'low', label: 'Low', description: 'Brief consideration' },
  { value: 'medium', label: 'Medium', description: 'Moderate analysis' },
  { value: 'high', label: 'High', description: 'Deep thinking' },
  { value: 'ultrathink', label: 'Ultra Think', description: 'Maximum reasoning depth' }
] as const;

// ============================================
// Agent Profiles
// ============================================

// Default phase model configuration for Auto profile
// Uses GLM-4.7 across all phases for maximum quality
export const DEFAULT_PHASE_MODELS: PhaseModelConfig = {
  spec: 'glm-4-7',       // Best quality for spec creation
  planning: 'glm-4-7',   // Complex architecture decisions
  coding: 'glm-4-7',     // Highest quality implementation
  qa: 'glm-4-7'          // Thorough QA review
};

// Default phase thinking configuration for Auto profile
export const DEFAULT_PHASE_THINKING: import('../types/settings').PhaseThinkingConfig = {
  spec: 'ultrathink',   // Deep thinking for comprehensive spec creation
  planning: 'high',     // High thinking for planning complex features
  coding: 'low',        // Faster coding iterations
  qa: 'low'             // Efficient QA review
};

// ============================================
// Feature Settings (Non-Pipeline Features)
// ============================================

// Default feature model configuration (for insights, ideation, roadmap, github)
export const DEFAULT_FEATURE_MODELS: FeatureModelConfig = {
  insights: 'glm-4-7',     // Fast, responsive chat
  ideation: 'glm-4-7',     // Creative ideation
  roadmap: 'glm-4-7',      // Strategic planning
  githubIssues: 'glm-4-7', // Issue triage and analysis
  githubPrs: 'glm-4-7'     // PR review
};

// Default feature thinking configuration
export const DEFAULT_FEATURE_THINKING: FeatureThinkingConfig = {
  insights: 'medium',     // Balanced thinking for chat
  ideation: 'high',       // Deep thinking for creative ideas
  roadmap: 'high',        // Strategic thinking for roadmap
  githubIssues: 'medium', // Moderate thinking for issue analysis
  githubPrs: 'medium'     // Moderate thinking for PR review
};

// Feature labels for UI display
export const FEATURE_LABELS: Record<keyof FeatureModelConfig, { label: string; description: string }> = {
  insights: { label: 'Insights Chat', description: 'Ask questions about your codebase' },
  ideation: { label: 'Ideation', description: 'Generate feature ideas and improvements' },
  roadmap: { label: 'Roadmap', description: 'Create strategic feature roadmaps' },
  githubIssues: { label: 'GitHub Issues', description: 'Automated issue triage and labeling' },
  githubPrs: { label: 'GitHub PR Review', description: 'AI-powered pull request reviews' }
};

// Default agent profiles for preset model/thinking configurations
export const DEFAULT_AGENT_PROFILES: AgentProfile[] = [
  {
    id: 'glm-47',
    name: 'GLM-4.7 (Default)',
    description: 'GLM-4.7 with balanced thinking for general tasks',
    model: 'glm-4-7',
    thinkingLevel: 'medium',
    icon: 'Sparkles',
    isAutoProfile: true,
    phaseModels: {
      spec: 'glm-4-7',
      planning: 'glm-4-7',
      coding: 'glm-4-7',
      qa: 'glm-4-7'
    },
    phaseThinking: DEFAULT_PHASE_THINKING
  },
  {
    id: 'glm-46',
    name: 'GLM-4.6',
    description: 'GLM-4.6 uncensored narrative mode for creative responses',
    model: 'glm-4-6',
    thinkingLevel: 'low',
    icon: 'Zap'
  },
  {
    id: 'complex',
    name: 'Complex Tasks',
    description: 'For intricate, multi-step implementations requiring deep analysis',
    model: 'glm-4-7',
    thinkingLevel: 'ultrathink',
    icon: 'Brain'
  },
  {
    id: 'balanced',
    name: 'Balanced',
    description: 'Good balance of speed and quality for most tasks',
    model: 'glm-4-7',
    thinkingLevel: 'medium',
    icon: 'Scale'
  },
  {
    id: 'quick',
    name: 'Quick Edits',
    description: 'Fast iterations for simple changes and quick fixes',
    model: 'glm-4-6',
    thinkingLevel: 'low',
    icon: 'Zap'
  }
];

// ============================================
// Memory Backends
// ============================================

export const MEMORY_BACKENDS = [
  { value: 'file', label: 'File-based (default)' },
  { value: 'graphiti', label: 'Graphiti (LadybugDB)' }
] as const;
