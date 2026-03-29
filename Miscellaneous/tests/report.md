# Datalyze — Tests & baselines index

This file is the **short index** for validation and baseline evidence. Deep narrative, changelog, and expectations-vs-achieved metrics live in the main handoff doc.

## Primary handoff (read this first)

**[`Miscellaneous/Datalyze.md`](../Datalyze.md)** — Integration baseline after merge: what changed, how API + orchestrator + UI connect, **first successful run** metrics, **accuracy sheet**, and pointers to all evidence.

## Testing phase (manual / agent-driven campaigns)

**[`../Datalyze_Analysis_Testing_Playbook.md`](../Datalyze_Analysis_Testing_Playbook.md)** — Attach to Cursor or Claude Code with your custom instructions: server hygiene, browser-first checks, API/terminal fallbacks, **≥3 sequential batches**, weighted **90% accuracy** rubric, and per-campaign **`Miscellaneous/tests/playbook-runs/<slug>/report.md`**. Scratch under `playbook-runs/` is gitignored except each campaign’s `report.md`.

## Baseline captures

| Evidence                                                                                                   | Description                                                                                                                                                                          |
| ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [`../First Successful Run/`](../First%20Successful%20Run/)                                                 | Filesystem snapshot of the first **completed** UI-driven run (20/20 agents, ~90s). Includes `logs.txt` and full `google-kartavya_singh-save-20260329_012948-GAF2xGgJz5Xj_zd_/` tree. |
| [`2026-03-28_21-22-42_excel-sequential-e2e-report.md`](2026-03-28_21-22-42_excel-sequential-e2e-report.md) | Scripted API E2E using `Google_Dataset_Analytics_Sample.xlsx`, sequential orchestrator flags.                                                                                        |
| [`2026-03-28_21-22-42_excel-sequential-e2e.json`](2026-03-28_21-22-42_excel-sequential-e2e.json)           | Machine-readable summary for the same run.                                                                                                                                           |

## Agent and orchestrator reports (narrative)

| Report                                                                                                                                                                     | Topic                                     |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| [`../Datalyze Agent Specialization - Performance Report.md`](../Datalyze%20Agent%20Specialization%20-%20Performance%20Report.md)                                           | Specialization + verify-all style results |
| [`../Datalyze Orchestrator Runtime - Master Plan vs Implementation Report.md`](../Datalyze%20Orchestrator%20Runtime%20-%20Master%20Plan%20vs%20Implementation%20Report.md) | Master plan phase scores and gap list     |

## Orchestrator scratch artifacts

Timestamped smoke files may live under `Miscellaneous/tests/Orchestrator_tests/` when generated locally (often gitignored). The **tracked** narrative above stays in `Datalyze.md` and this index.

## Quick baseline numbers (first successful run)

- **Status:** `completed`
- **Agents:** 20/20 completed, 0 failed, 0 skipped
- **Duration:** ~89.8s (see `First Successful Run/.../final_report.json`)
- **Track:** `predictive`
