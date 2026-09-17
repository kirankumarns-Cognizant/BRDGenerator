# Defect Resolution Agent — Design & Workflow

An agent that takes a production ticket and answers the question that actually matters:
**how do we fix this, and where?** — with citations to the BRD, repository, execution
flow, endpoint and code location.

---

## 1. The problem this solves

The first version of the agent produced a five-section RCA. It described *what*
happened, never *what to change*. Measured on the July sheets, **86 of 92 rows** came
back as "No Action Taken — Requires analysis".

Root causes, all measurable:

| Failure | Evidence |
| --- | --- |
| No fix-generation path existed | The RCA template had 5 hard-coded sections, none of them a resolution |
| Logs retrieved but not read | Queries asked for 100 hits and consumed `hits[0]`, unsorted; 6,452 extractions yielded **5** error messages and **0** failure localizations. The most common "sample log" fed to the model was the string `Outbound Payload` (2,794×) |
| KB effectively empty | ~100 embedded chunks for 114 BRDs / 6.9 MB, so every ticket retrieved the same irrelevant sections |
| Fix-level assets never opened | BRD `Repo:` URLs, the Business Rules Catalog, Endpoint→Rule maps, `call_stack.db` (16.7 MB) and `hypergraph.json` (18k edges) were on disk and read by no code |
| The classifier disqualified its own output | The conclusion wrote "Functional context was unavailable"; the classifier treated that exact phrase as a "requires analysis" marker |
| No procedural knowledge | Even with evidence, nothing told the agent *how* to turn evidence into a fix |

The last point is why **Skills** matter, and the third and fourth are why **BRDs**
matter. Neither works without the other.

---

## 2. Why defect resolution needs the BRD

Logs tell you *where it broke*. The BRD tells you *what should have happened* — and a
fix is only definable as the delta between the two.

1. **A fix requires intended behaviour.** A log line `NullPointerException mapping DMD
   feature list` proves a crash. Whether the fix is "guard the null and return business
   error VZ-4021" or "the upstream must always populate featureList" is a *specification*
   question. Only the BRD answers it.
2. **The BRD is the only artifact that maps symptom → owning service → repository.**
   Runtime logs give you `app_name`; the BRD's `Repo:` metadata turns that into a GitLab
   URL a developer can open. Without it the recommendation stops at "something in
   ordering is wrong".
3. **Business rules make the fix reviewable.** Citing rule IDs and validator chains lets
   a reviewer confirm the proposed change does not violate another rule — the difference
   between a suggestion and an actionable defect.
4. **Endpoint→Rule maps and call stacks localize inside the service.** A service name is
   not a fix location; a class, endpoint and flow step is.
5. **It disambiguates identical symptoms.** "SIM already active" in reactivation and in
   device swap are different defects with different owners. The BRD journey/flow sections
   separate them.
6. **It covers the gaps logs cannot.** Timeouts, config values and missing-record cases
   leave no exception. The documented SLA, config contract or persistence rule is the
   only evidence that the observed behaviour is wrong.

Put simply: **logs prove the failure, the BRD defines the correction, Skills supply the
procedure, and the call stack points at the line.** Remove any one and the output degrades
back to "needs more information".

---

## 3. Architecture

```
                            ┌──────────────────────────┐
   ticket row (xlsx/csv) ──→ │  DefectResolutionAgent   │
                            └────────────┬─────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
┌───────────────────┐        ┌────────────────────────┐        ┌────────────────────┐
│ JiraEvidence      │        │ OpenSearchLogSearch    │        │ SkillLibrary       │
│ Collector (MCP)   │        │ + LogEvidence (MCP)    │        │ skills/*/SKILL.md  │
│ whole issue,      │        │ every hit, error-first │        │ evidence + fix     │
│ symptom search    │        │ ranked, aggregated     │        │ procedures         │
└─────────┬─────────┘        └───────────┬────────────┘        └─────────┬──────────┘
          │                              │                               │
          └──────────────┬───────────────┘                               │
                         ▼                                              │
              ┌──────────────────────┐                                   │
              │ FixContextResolver   │  BRD embeddings (kb_store)        │
              │ services, repos,     │  call_stack.db, hypergraph.json   │
              │ rules, endpoints,    │                                   │
              │ symbols, code paths  │                                   │
              └──────────┬───────────┘                                   │
                         └──────────────┬────────────────────────────────┘
                                        ▼
                        ┌───────────────────────────────┐
                        │ ResolutionSynthesizer         │
                        │ failure class → fix template  │
                        │ + EvidenceProfile (structured)│
                        └───────────────┬───────────────┘
                                        ▼
                    six-section RCA  +  Issue Resolution class
                    + Recommended Fix / Fix Location / Repository / Confidence
```

---

## 4. Workflow — high-level steps

**Step 0 — Read the row.** Symptom plus the technical columns the workbook keeps beside
it (`Error Info`, `Flow`, `Comments`, `Root Cause`). Extract the defect key, or note it is `NA`.

**Step 1 — Retrieve the complete Jira issue.**
Summary, description, *all* comments, status, resolution, components, labels, links,
subtasks, attachments, changelog, custom fields, environment, versions. Mine it for
exception names, HTTP statuses, endpoints, stack frames, failure sentences and
identifiers (MDN, ESN, e2eRequestId). When the row's defect field is `NA`, run a
symptom-based JQL search and report candidate keys instead of giving up.

**Step 2 — Retrieve *all* the logs.**
Query indices `k18v* k0cv* k2nv* k16v*` per identifier, paging rather than sampling.
Every returned document is parsed and scored:
- ERROR/FATAL level, 4xx/5xx status and error keywords raise severity;
- success-status documents whose payloads merely *contain* the word "error" (empty
  `"errorCode":null` slots) are damped — this was the largest false-positive source;
- generic envelopes (`Inbound Payload`) are replaced with the real error text dug out of
  the payload.
Then aggregate: failure count, repeated signatures with masked identifiers, error codes,
failing services, code paths, HTTP errors, flows, correlation IDs. Authentication
failures stay visible as an evidence gap — they are never silently converted to "no logs".

**Step 3 — Ground it in the BRD.**
Hybrid dense + BM25 retrieval over the BRD chunks, boosting `business_rule`,
`endpoint_rule_map`, `validator_chain` and `call_stack` sections, with per-service
diversity caps. Candidate services are scored from three sources with different weights —
logs 3.0 (runtime truth), Jira 2.0 (ownership), BRD 1.0 (documentation). Then
`call_stack.db` and the hypergraph expand the flow: steps, downstream dependencies,
related services. Output: candidate services, repository URLs, rule IDs, endpoints,
symbols, concrete code paths — and explicit gaps for whatever is missing.

**Step 4 — Select Skills.**
Load `skills/*/SKILL.md`, select orchestrator + domain skills by defect text, service,
repo, component and category, and record *why* each was selected. Extract
evidence-collection directives, root-cause validation guidance and fix/remediation
patterns to steer the next step.

**Step 5 — Synthesize the resolution.**
Classify the failure into one of eight modes — unguarded dereference while mapping,
timeout, auth rejection, over-strict validation, downstream 5xx, missing record,
duplicate/idempotency, configuration — each carrying a fix template and a verification
step. Fill the template with the localized change site, attach repository, BRD, rule,
flow, endpoint and symbol references, and score confidence from the structured evidence.

**Step 6 — Classify from structure, not prose.**
An `EvidenceProfile` of booleans (`has_error_payload`, `failure_localized`, `brd_match`,
`repo_target`, `candidate_fix`, `retrieval_blocked`) drives the workbook's Issue
Resolution value. Prose is consulted only to detect *intent* (training vs. DB cleanup).
A row can no longer be demoted because of a phrase in its own narrative.

**Step 7 — Emit.**
Six-section RCA — `TICKET OVERVIEW`, `LOG ANALYSIS`, `JIRA DEFECT`,
`GROUNDED FUNCTIONAL INSIGHT`, **`RESOLUTION`**, `CONCLUSION` — plus columns
`Recommended Fix`, `Fix Location`, `Repository`, `Resolution Confidence`, `Open Gaps`.

---

## 5. The RESOLUTION contract

Three outcomes, never blurred:

| Status | Meaning | Output |
| --- | --- | --- |
| `resolution_proposed` | Error payload **and** failure localization present | Root cause, fix, change site, repo, references, verification, confidence |
| `analysis_required` | Evidence retrieved but incomplete | The *specific* missing signal and the next step (e.g. "obtain the e2eRequestId for the failing transaction") |
| `evidence_blocked` | We could not look — auth failure or MCP down | The operational blocker, e.g. "restore OpenSearch credentials; every query was rejected" |

The distinction between "we looked and the evidence is thin" and "we could not look" is
deliberate: the first is a data problem for the analyst, the second an infrastructure
problem for the platform team. The old agent reported both as "requires analysis".

---

## 6. Evidence assets

| Asset | Size | Used for |
| --- | --- | --- |
| BRD Markdown (`KB/brd`) | 114 docs → **8,173 chunks**, 108 services | Intended behaviour, business rules, repo URLs, endpoint→rule maps |
| `call_stack.db` | 1,676 nodes / 3,256 edges | Flow steps, symbols, downstream dependencies |
| `hypergraph.json` | 249 nodes / ~18k edges | Cross-document/service relationships |
| `skills/*/SKILL.md` | 55 skills | Evidence-collection and fix procedures |
| OpenSearch | `k18v* k0cv* k2nv* k16v*` | Runtime failure and localization |
| Jira | `https://onejira.verizon.com` | Symptom, history, human analysis, identifiers |

---

## 7. Results

Measured on the two supplied workbooks with mocked MCP connectors replaying 2,601 real
OpenSearch documents:

| Sheet | Before | After |
| --- | --- | --- |
| July 22 (98 rows) | ~6 actionable | **60 rows with a concrete fix** |
| July 29 (96 rows) | 86/92 "requires analysis" | **81 rows with a concrete fix**, 82 reclassified |

Remaining rows are not generic — each names the missing signal and the next step.
Validation: 128 tests covering each fix in isolation plus end-to-end runs of both
workbooks and the orchestrator; a clean checkout rebuilds the KB store and passes.

---

## 8. POV talking points

- **The bottleneck was never the model.** No LLM ever saw a real error message; the
  pipeline discarded 99 of every 100 log documents before reasoning began. Fix retrieval
  before you fix prompts.
- **Documentation is an executable asset.** BRDs were treated as reading material.
  Chunked, embedded and indexed by rule/endpoint/repo, they become the specification the
  agent diffs runtime behaviour against — the step that converts an RCA into a fix.
- **Skills are the missing procedural layer.** Evidence plus specification still needs a
  method; Skills encode how your engineers actually localize and remediate.
- **Classify on structured evidence, never on your own prose.** Narrative-driven
  classification is self-reinforcing and silently collapses to the fallback bucket.
- **Honest gaps beat confident guesses.** Naming the one missing artifact ("we need the
  e2eRequestId") is actionable; "more information needed" is not.
- **Traceability is the adoption lever.** Every recommendation carries BRD, repo, flow,
  endpoint and symbol references, so a developer can verify it in minutes rather than
  re-doing the analysis.
