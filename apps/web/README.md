# Web App (`apps/web`)

Vite + React + TypeScript frontend for Datalyze.

## Purpose

- Host onboarding, dashboard, graph, and export UI.
- Talk to backend API routes through `/api/*`.
- Keep feature modules organized by business domain.

## Current Files

- `src/App.tsx`: connectivity starter page and API ping UI.
- `src/lib/api.ts`: typed API client utilities.
- `src/styles/index.css`: base styling.
- `vite.config.ts`: dev server + backend proxy config.

## Suggested Next Implementations

- `src/features/onboarding`: onboarding flow and wizard state.
- `src/features/dashboard`: cards, charts, logs, and graph.
- `src/features/chat`: conversational analysis panel.
- `src/components`: reusable UI primitives.
