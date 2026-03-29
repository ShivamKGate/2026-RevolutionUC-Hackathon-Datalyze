# Excel Sequential E2E Validation Report

## Test objective

Validate one complete, end-to-end analysis run using the Excel fixture through the real application APIs:

1. user setup with selected theme
2. Excel upload
3. orchestrator start
4. sequential stage-by-stage dispatch
5. synthesis/insight generation
6. finalized replay-ready run artifacts

## Run metadata

- Timestamp: `2026-03-28_21-22-42`
- Fixture: `Miscellaneous/data/sources/Google_Dataset_Analytics_Sample.xlsx` (76,167 bytes)
- Saved raw evidence: `Miscellaneous/tests/2026-03-28_21-22-42_excel-sequential-e2e.json`
- Run slug: `bDRKt930Cz0DWf1_`
- Run directory: `data/pipeline_runs/predictive/e2e_analytics_co-e2e_user-save-20260329_012242-bDRKt930Cz0DWf1_`

## Configuration under test

- Track selected by user: `deep_analysis` onboarding path
- Resolved run track: `predictive`
- Parallel mode: `false`
- Adaptive mode: `false`
- Stage gates: `true`
- Max run seconds: `900`

## Completion result

- Final status: `completed`
- Summary: `Track: predictive | Status: completed | Completed: 20/20 agents | Duration: 239.9s`
- Stage starts observed: `7`
- Agent dispatches observed: `20`
- Agent completions observed: `20`
- Total run log rows: `56`
- Decision ledger rows: `20`

## Sequential flow verification

Decision ledger confirms strict sequential dispatch (no parallel fan-out). Start and end of sequence:

- First 5 dispatched: `pipeline_classifier`, `file_type_classifier`, `pdf_processor`, `csv_processor`, `excel_processor`
- Last 5 dispatched: `knowledge_graph_builder`, `insight_generation`, `swot_analysis`, `executive_summary`, `elevenlabs_narration`

Stage progression observed in logs:

1. `classify`
2. `ingest`
3. `process`
4. `aggregate`
5. `analyze`
6. `synthesize`
7. `finalize`

## Insight and output validation

- `insight_generation` completed: **true**
- `executive_summary` completed: **true**
- Final report status: `completed`
- Executive summary content present and business-facing (predictive trend, SWOT, risk signals)
- Replay payload returned with keys: `run`, `logs`, `replay_payload`

## Functional findings

### What worked as intended

- Full run reached terminal success from upload to finalization.
- Orchestrator made end-to-end dispatch decisions and completed all planned stages.
- Sequential flow held for the whole run (as configured).
- Final report and replay artifacts were persisted and queryable.

### Gaps identified (important)

1. **Classifier fallback path used**
   - Pipeline classifier completed with: `Track classified (rule-based fallback): predictive`.
   - This happened because Gemini quota was exhausted in this environment.
   - Impact: run still succeeded, but external classifier path was not validated in this test.

2. **File-type classifier output quality mismatch**
   - Output snippet indicated synthetic routing (`file1.pdf`, `file2`) not directly matching uploaded Excel filename.
   - Despite this, Excel processor still executed in the orchestrated stage and pipeline completed.
   - Impact: potential signal-quality issue for routing fidelity, though not a blocker to completion.

3. **ElevenLabs handoff context issue**
   - `elevenlabs_narration` completed with message: `No executive summary available for narration`.
   - But `executive_summary` had already completed with non-empty summary text.
   - Impact: audio generation path is not receiving required context at dispatch time.

## Verdict

The requested deep single-run sequential E2E test **passes for core orchestration and insight generation**:

- Excel import worked
- Orchestrator-to-finalize lifecycle completed
- Insights and executive summary were produced
- Replay and run artifacts were generated

At the same time, there are **three concrete integration-quality issues** (Gemini fallback dependence, file-routing fidelity, ElevenLabs context handoff) that should be treated as next hardening tasks.
