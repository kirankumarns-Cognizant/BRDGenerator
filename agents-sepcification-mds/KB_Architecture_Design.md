**ENTERPRISE KNOWLEDGE LAYER**

*Architecture Design Document*

KB Store  ·  RAG Layer  ·  LightRAG  ·  Confluence  ·  Artifact Registry

SDLC Agentic Framework  |  Version 1.0  |  Design Baseline

---

# Design Story — How It All Flows
---Imagine a senior architect who has worked on every migration, reviewed every BRD, debugged every defect, and remembers every decision ever made. They know which artifacts to look at for any question, why each business rule exists, how the same concept differs across brands, and what failed before. That is the Knowledge Layer. Except it never leaves, never forgets, and gets smarter every day.



| **An agent runs. Knowledge is created. The brain grows. The next agent starts smarter.** |
| :---: |
## The Story — From Agent Run To Answered Query
Here is the full journey of a piece of knowledge — from agent output to answered query — told as a story.
### Chapter 1 — An Agent Produces Knowledge
The BRD Agent finishes analyzing the StraightTalk service ordering repo. It drops structured JSON files into its output folder — journey_map.json, business_rules.json, gap_analysis.json. It does not know about the Knowledge Layer. It just produced artifacts and moved on.
### Chapter 2 — KB Store Picks It Up
KB Store triggers automatically. It reads the folder. It renames each file following the naming convention — ST_SO_Activation_journey_map_v1.json. It calls the LLM to extract metadata — what is this artifact, who produced it, what is it useful for, what entities does it mention. It creates a UUID for each artifact and logs it in the registry.
### Chapter 3 — The Placement Agent Thinks
For each artifact, the placement agent reasons: does a node already exist for StraightTalk / Service Ordering / Activation? Yes — append this artifact's UUID to that node. Does a cross-brand relationship exist between ST and TW Activation? Not yet — create a hyperedge connecting them, note the differences, send a notification for human review. One artifact that cannot be classified cleanly — create a TEMP node, write to notifications.json, move on without blocking.
### Chapter 4 — Three Surfaces Updated
The JSON artifact is written to KB/StraightTalk/ServiceOrdering/Activation/. The Confluence page for that feature is updated with a new entry in the TOC. The hypergraph node for node_ST_SO_Activation gains a new artifact UUID. All three surfaces now reflect the same knowledge — machine, human, and navigation layers in sync.
### Chapter 5 — A Query Arrives
Three weeks later a QA engineer asks: 'How does the activation flow work for StraightTalk?' The query is embedded. The intent is classified: service_ordering, brand ST, topic activation. The alias index in the hypergraph is checked — 'activation' maps to node_ST_SO_Activation. The node returns three artifact UUIDs.
### Chapter 6 — Targeted Retrieval
LightRAG searches only the embeddings for those three artifacts — not the entire vector store. It finds the relevant chunks in the journey_map and business_rules artifacts. It assembles the answer. The answer is returned to the engineer with HIGH confidence and source attribution pointing to the exact artifacts.
### Chapter 7 — The Brain Gets Smarter
The write-back function runs in the same LLM call. The journey_map artifact's metadata is updated: access_count now 4, used_for includes test_case_writing, query_intents includes service_ordering_activation. The query is logged in query_log.json. Next time someone asks about activation — the system already knows this artifact is the most useful one.
### Chapter 8 — Eventually — The Cache
In production — Phase 2 — the same query arrives again. The FAQ cache finds it at 0.94 cosine similarity. The source artifacts have not changed. The cached answer is returned instantly at near-zero cost. No RAG. No LLM. The knowledge is just there.

## The Full Flow — At A Glance


| `  ┌─────────────────────────────────────────────────────────────────────┐``  │                         KNOWLEDGE LAYER FLOW                        │``  └─────────────────────────────────────────────────────────────────────┘``  WRITE PATH (KB Store — triggered after every agent run)``  ─────────────────────────────────────────────────────``  Agent Output Folder``       |``       v``  [1] Artifact Receiver     reads files from configured path``       |``       v``  [2] Artifact Renamer      ST_SO_Activation_journey_map_v1.json``       |``       v``  [3] Metadata Extractor    UUID, producer, domain, tags, confidence``       |``       v``  [4] Conflict Resolver     duplicate? overwrite? HITL? keep both?``       |``       v``  [5] Placement Agent       which hypergraph node? new? temp? merge?``       |                    notification if unsure → non-blocking``       |``       +──────────────────────────────────────┐``       |                                       |``       v                                       v``  [6] JSON Writer           [7] Confluence Sync  [8] Registry Writer``  KB/Brand/Domain/Feature/  Mirrors hypergraph    artifact_registry.db``  artifact_v1.json          page hierarchy        metadata + lineage``                                    |``                                    v``                            Hypergraph Updated``                            node gets new UUID``                            alias index updated``  ─────────────────────────────────────────────────────``  READ PATH (RAG Component — when query arrives)``  ─────────────────────────────────────────────────────``  Query: 'How does activation work for StraightTalk?'``       |``       v``  [1] Intent Recognition    domain=service_ordering, brand=ST``       |                    keywords: activation, StraightTalk``       v``  [2] Alias Index Lookup    'activation' → node_ST_SO_Activation``       |``       v``  [3] Get Artifact UUIDs    [abc123, def456, ghi789]``       |``       v``  [4] Targeted Vector       search ONLY those 3 artifact embeddings``      Search (LightRAG)     not the entire vector store``       |``       +──── Found? ──── YES → Answer + HIGH confidence``       |                        + write-back to metadata``       |                        + log to query_log.json``       |``       +──── Found? ──── NO  → Brute force RAG on all embeddings``                                Answer + LOW confidence label``                                'This is all I found but``                                 could not pinpoint the source'``  ─────────────────────────────────────────────────────``  PHASE 2 — FAQ CACHE (Production — not POC)``  ─────────────────────────────────────────────────────``  Same query arrives again``       |``       v``  Cosine similarity > 0.92 AND source docs unchanged?``       |``       +── YES → Return cached answer. Zero RAG. Zero LLM cost.``       +── NO  → Run RAG, update cache, serve fresh answer.` |
| --- |
# 1. Purpose & Vision
---

| **The Knowledge Layer is the enterprise intelligence infrastructure that serves every agent in the SDLC pipeline — now and in the future.***It is not a document store. It is a reasoning layer that gets smarter every time it is used.* |
| :---: |
Every agent in the SDLC pipeline — BRD Agent, Coding Agent, QA Agent, Defect Triage Agent — produces structured artifacts. The Knowledge Layer receives these artifacts, organizes them, makes them available to humans via Confluence, to tools via structured JSON, and to agents via LightRAG-powered natural language retrieval. It learns from every interaction and gets more precise over time.

The design is intentionally client-agnostic. Value enterprise today. Verizon tomorrow. Any open source repo next week. The domain context is fed via a configurable JSON file — the infrastructure is the same.
## 1.1  What It Is Not
- Not a static document repository — it learns and evolves

- Not agent-specific — it serves every agent and every human

- Not fixed-schema — metadata grows as we learn more about each artifact

- Not tied to one client or domain — domain knowledge is fed externally via config

- Not one-directional — it writes back from queries to enrich artifact metadata

# 2. Architecture Overview
---

| `  ┌─────────────────────────────────────────────────────────────────────┐``  │                    KNOWLEDGE LAYER                                   │``  │                                                                     │``  │  ┌─────────────────────────────────────────────────────────────┐   │``  │  │  INGESTION LAYER (KB Store Component)                        │   │``  │  │  Receives artifacts → renames → extracts metadata            │   │``  │  │  Placement Agent → Hypergraph update                         │   │``  │  │  Resolves conflicts → writes to all storage layers           │   │``  │  └──────────────────────────┬──────────────────────────────────┘   │``  │                              │                                       │``  │         ┌────────────────────┼──────────────┬──────────┐           │``  │         ▼                    ▼              ▼           ▼           │``  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐   │``  │  │  Confluence   │  │  JSON Files  │  │ Registry │  │Hypergraph│   │``  │  │  Human Layer  │  │  Tool Layer  │  │ SQLite / │  │ JSON /   │   │``  │  │  Mirrors      │  │  Copilot,    │  │ JSON     │  │ SQLite / │   │``  │  │  hypergraph   │  │  CLI, tools  │  │ metadata │  │ Kuzu     │   │``  │  │  structure    │  │              │  │ lineage  │  │ Nav layer│   │``  │  └──────────────┘  └──────────────┘  └──────────┘  └──────────┘   │``  │                                                           │          │``  │  ┌────────────────────────────────────────────────────────▼──────┐  │``  │  │  RAG LAYER (Separate Component — built after KB Store)         │  │``  │  │                                                                │  │``  │  │  Query → Intent Recognition → Hypergraph Navigation            │  │``  │  │        → Get artifact UUID list → Targeted Vector Search       │  │``  │  │        → Answer (HIGH confidence) + write-back                 │  │``  │  │        → Fallback: brute force RAG (LOW confidence label)      │  │``  │  │                                                                │  │``  │  │  LightRAG: Entity graph within docs + Vector Store            │  │``  │  └────────────────────────────────────────────────────────────────┘  │``  └─────────────────────────────────────────────────────────────────────┘` |
| --- |
## 2.1  The Four Storage Layers


| **Confluence** | Human reading layer. Structured pages mirroring the hypergraph structure exactly — Brand → Domain → Feature → Artifact. TOC with navigation links auto-generated. Where BAs, architects, engineers browse and validate. HITL decisions supported here. Updated whenever hypergraph structure changes. |
| --- | --- |
| **JSON Files** | Machine consumption layer. Structured artifacts for direct tool consumption — GitHub Copilot, Claude CLI, Playwright generators. These tools need clean structured input passed directly. No RAG needed. Fast, cheap, direct. |
| **Registry (SQLite / JSON)** | Master index of every artifact ever produced. Artifact ID, name, lineage, usage history, intent tags, SVM training labels, confidence. The appendix and TOC of the enterprise knowledge base. Handles concurrent writes via SQLite WAL mode. |
| **Hypergraph (JSON / SQLite / Kuzu)** | Navigation layer. Groups artifacts by feature, domain, brand into nodes and hyperedges. The folder system for the knowledge base. RAG queries this first to get a targeted artifact list before searching any embeddings. Confluence mirrors this structure. Upgrade path: JSON → SQLite → Kuzu. |
## 2.2  The RAG Layer (Separate — Built After KB Store)


| **Step 1 — Intent Recognition** | Query arrives. LLM classifies: what domain, what brand, what topic. Keywords extracted. For POC — LLM prompt. Later — SVM trained on query_intents accumulated in registry metadata. |
| --- | --- |
| **Step 2 — Hypergraph Navigation** | Intent and keywords matched against alias index in hypergraph. Returns matching node(s) or hyperedge(s). Gets artifact UUID list for those nodes. This is the folder navigation — go to the right shelf before searching. |
| **Step 3 — Targeted Vector Search** | Search ONLY embeddings for the artifact UUIDs returned by hypergraph. LightRAG searches within those targeted chunks. Not the entire vector store. High precision, low noise, low cost. |
| **Step 4 — Answer + Write-back** | Answer returned with source attribution and HIGH confidence label. Same LLM call returns write-back payload. kb_writeback() updates artifact metadata. Session context updated. |
| **Fallback — Brute Force RAG** | If targeted search returns no answer — drop hypergraph navigation. Run standard RAG on all embeddings. Return whatever is most semantically similar. Label answer as LOW confidence. Tell user: this is all I found but I could not pinpoint the source. |
| **LightRAG Role** | Handles entity-level graph WITHIN documents and chunk-level vector retrieval. Does NOT handle the document-group navigation — that is the hypergraph's job. LightRAG works within the targeted artifact set the hypergraph provides. |
| **Session Context** | Within active session — conversation history maintained. Prior queries and retrieved artifacts inform subsequent queries. Cleared when session ends. |
# 3. The Two Components
---

| **KB Store Component — build first. RAG Component — build second.***Once KB Store is right, RAG plugs on top cleanly. Separation prevents getting lost and gives developers something working faster.* |
| :---: |
## 3.1  KB Store Component
Standalone pipeline component. Receives agent output artifacts from a configured folder path. Renames per convention, extracts metadata, resolves conflicts, writes to all three storage layers. Does not know which agent ran or what domain it is — it just consumes a path.

| `  Agent runs → produces artifacts in output folder``        |``        v``  KB Store Component triggers``  (Auto: fires after agent completes)``  (Manual: python kb_store.py --path ./KB/artifacts/)``        |``        +── Artifact Receiver    reads from configured path``        +── Artifact Renamer     applies naming convention``        +── Metadata Extractor   creates metadata node``        +── Conflict Resolver    checks registry for duplicates``        +── Lineage Tracker      links derived_from relationships``        |``        +── JSON Writer          writes to folder structure``        +── Confluence Sync      creates / updates pages + TOC``        +── Registry Writer      updates artifact_registry.db``        |``        v``  KB enriched. Ready for RAG layer.` |
| --- |
**Entry Criteria:** Agent has completed its run and produced output artifacts in a known folder path. OR manual path provided via --path argument.

**Exit Criteria:** All artifacts renamed, metadata extracted, conflict resolved, written to JSON folder, Confluence pages created/updated, artifact_registry.db updated, lineage recorded.

**Trigger Modes:** Auto — runs immediately after agent completes as part of pipeline. Manual — standalone execution with --path argument for retroactive ingestion of existing artifacts.

## 3.2  RAG Component
Built after KB Store is stable. Sits on top of the storage layers KB Store produces. Handles natural language queries from agents, humans, and HITL decision support. Uses LightRAG for graph-guided, targeted retrieval.

**Entry Criteria:** KB Store has run and artifacts are stored. Embeddings generated for all artifacts. LightRAG graph initialized with domain config.

**Exit Criteria:** Query answered with source attribution. Write-back payload returned and written to artifact metadata. Session context updated.

**Embedding Strategy:** All artifacts embedded at ingestion time during KB Store run — not at query time. Only new artifacts generate new embeddings on subsequent runs. Existing embeddings reused.

# 4. Naming Convention & Folder Structure
---## 4.1  Artifact Naming Convention
Every artifact produced by any agent in any context follows this naming pattern. The name alone tells you everything without opening the file.

| **Naming Pattern**`{brand}_{domain}_{feature}_{artifact_type}_v{version}.{ext}`**Examples:**`ST_ServiceOrdering_Activation_journey_map_v1.json``TW_Payments_Subscription_business_rules_v2.json``SHARED_Identity_Authentication_actor_definitions_v1.json``ST_ServiceOrdering_Activation_brd_final_v1.docx``EXT_openrepo_OrderMgmt_test_cases_v1.json` |
| --- |
## 4.2  Brand Prefix Codes


| **ST** | StraightTalk |
| --- | --- |
| **TW** | TotalWireless |
| **TF** | TracFone |
| **WFM** | Walmart Family Mobile |
| **SHARED** | Applies across multiple brands — common elements |
| **VALUE** | Value enterprise level — cross-brand, cross-domain |
| **EXT** | External or open source repo |
| **CLIENT** | Template prefix — replace CLIENT with client code for new engagements |
## 4.3  Artifact Type Codes


| **journey_map** | All user and system journeys — BRD Agent output |
| --- | --- |
| **business_rules** | Extracted and plain-Englished business rules — BRD Agent output |
| **gap_analysis** | Legacy vs NSA capability gaps — BRD Agent output |
| **brd_final** | Locked Business Requirements Document — BRD Agent final output |
| **scope_definition** | Component scope boundaries — BRD Agent output |
| **test_cases** | Test case specifications — QA Agent output |
| **ac_criteria** | Acceptance criteria in Given/When/Then format — BRD/QA Agent output |
| **code_review** | Code review findings — Coding Agent output |
| **defect_analysis** | Defect root cause and triage — Defect Triage Agent output |
| **actor_definitions** | Actor and role definitions — BRD Agent output |
| **dependency_map** | System and data dependencies — BRD Agent output |
| **risk_register** | Risk register with scores — BRD Agent output |
| **regression_gaps** | Gaps between ACs and existing test coverage — QA Agent output |
| **api_spec** | API contract specifications — Architecture/Coding Agent output |
| **story_brief** | Feature story or grooming brief — Story Agent output |
## 4.4  Folder Structure


| `  KB/``  ├── domain_config/``  │   ├── value_domain.json          # Value enterprise context + ontology seed``  │   ├── postpaid_domain.json       # Client-specific domain config``  │   └── {client}_domain.json       # Template for new client``  │``  ├── StraightTalk/                  # Mirrors Confluence Brand page``  │   ├── ServiceOrdering/           # Mirrors Confluence Domain page``  │   │   ├── Activation/            # Mirrors Confluence Feature page``  │   │   │   ├── ST_SO_Activation_journey_map_v1.json``  │   │   │   ├── ST_SO_Activation_business_rules_v1.json``  │   │   │   ├── ST_SO_Activation_gap_analysis_v1.json``  │   │   │   ├── ST_SO_Activation_ac_criteria_v1.json``  │   │   │   ├── ST_SO_Activation_test_cases_v1.json``  │   │   │   ├── ST_SO_Activation_risk_register_v1.json``  │   │   │   └── ST_SO_Activation_brd_final_v1.docx``  │   │   └── PortIn/``  │   │       └── ...``  │   └── Payments/``  │       └── ...``  │``  ├── TotalWireless/``  │   └── ServiceOrdering/           # Same domain — hypergraph links to ST``  │       └── ...``  │``  ├── SHARED/``  │   ├── Identity/``  │   │   └── SHARED_Identity_actor_definitions_v1.json``  │   └── Payments/``  │       └── SHARED_Payments_gateway_rules_v1.json``  │``  ├── EXT/``  │   └── {repo_name}/{feature}/``  │       └── EXT_repo_feature_brd_final_v1.json``  │``  ├── graph/``  │   ├── hypergraph.json            # Navigation layer — nodes, hyperedges, alias index``  │   │                              # POC: JSON / Production: SQLite / Enterprise: Kuzu``  │   ├── notifications.json         # Async placement decisions needing human review``  │   └── lightrag/                  # LightRAG storage (RAG component)``  │       ├── graph_chunk_entity_relation.graphml``  │       ├── kv_store_*.json``  │       └── vdb_*/                 # Vector DB chunks per artifact``  │``  └── registry/``      ├── artifact_registry.db       # SQLite — master artifact index``      └── artifact_registry.json     # JSON fallback if SQLite not configured` |
| --- |
# 5. Artifact Registry & Metadata
---

| **The artifact registry is the nervous system of the enterprise knowledge layer.***Not for reading content — for knowing where content is, what it is for, and what it has been used for.* |
| :---: |
## 5.1  Registry Design — SQLite
The artifact registry lives in a single SQLite database: KB/registry/artifact_registry.db. SQLite is chosen because it handles concurrent writes natively via transactions, is local and zero-dependency, human-inspectable via any SQLite viewer, and exportable to JSON at any time. For POC — one database. For production — same design, hosted database if concurrent write pressure demands it.

| **Registry Storage****Decision:** SQLite (artifact_registry.db)**Why:** *Handles concurrent writes from parallel agent runs natively via transactions. Local, zero-dependency, human-inspectable. Exportable to JSON. Same schema works for POC through production.* |
| --- |
## 5.2  Artifact ID Design
Every artifact gets a UUID generated as: timestamp_utc + uuid4 short suffix. This makes IDs sortable by creation time, unique across parallel runs in any timezone, and traceable to when they were created.

| **Artifact ID Format**`{YYYYMMDD_HHMMSS_UTC}_{uuid4_8chars}``Example: 20260511_143022_UTC_a3f9bc12`Human-readable name sits alongside the ID as a separate field. Name used for display and reference. ID used as the unique key for all internal linking. |
| --- |
## 5.3  Metadata Schema — Sparse, Evolving
Metadata is not a fixed schema. It starts with what is known at creation time and grows as the artifact is used. Fields that are unknown at creation are simply absent — not null, not empty string — absent. This keeps the metadata honest and allows it to evolve without schema migrations.
### At Creation — What We Know


| **artifact_id** | UUID — unique key. Never changes. |
| --- | --- |
| **name** | Human-readable name following naming convention |
| **artifact_type** | journey_map | business_rules | gap_analysis | brd_final | test_cases | etc. |
| **producer_agent** | Which agent produced this — brd_agent | qa_agent | coding_agent | human | etc. |
| **producer_run_id** | Run ID from the agent run that produced this |
| **brand** | ST | TW | TF | WFM | SHARED | EXT | VALUE |
| **domain** | service_ordering | payments | identity | catalog | etc. |
| **feature** | Specific feature or component within the domain |
| **repo** | Source repository name |
| **version** | Version number — v1, v2 etc. |
| **format** | json | docx | feature | md |
| **file_path** | Relative path in KB folder structure |
| **confluence_url** | URL of corresponding Confluence page — added after sync |
| **confidence** | HIGH | MEDIUM | LOW — from producing agent |
| **created_at** | UTC timestamp |
| **derived_from** | List of artifact_ids this was derived from — lineage tracking |
| **client** | Value | Verizon | EXT | etc. |
### Grows Over Time — As We Learn


| **used_for** | List of task types this artifact has helped with — test_case_writing | code_generation | defect_triage | architecture_decision | hitl_support |
| --- | --- |
| **query_intents** | List of query intent labels that retrieved this artifact — becomes SVM training data |
| **hitl_decisions_informed** | List of HITL decision IDs where this artifact provided supporting facts |
| **co_retrieved_with** | Artifact IDs frequently retrieved alongside this one — co-retrieval patterns |
| **usefulness_scores** | Per task type — how often this was actually used vs retrieved but ignored |
| **last_accessed** | UTC timestamp of most recent retrieval |
| **access_count** | Total number of times retrieved |
| **updated_at** | UTC timestamp of last metadata update |
| **superseded_by** | Artifact ID of newer version if this is outdated |
| **entity_tags** | Business entities LightRAG extracted from this artifact content |
| **cross_brand_relevance** | Other brands this artifact was found relevant for |
| **alias** | Alternative names or references for this artifact |
| **notes** | Free text — human or agent observations about this artifact over time |
# 6. Conflict Resolution
---When a new artifact arrives, the KB Store checks the registry for potential conflicts before writing. Conflict resolution is handled by a sub-agent with defined house rules. It resolves autonomously where possible and escalates to HITL only when genuinely ambiguous.
## 6.1  Conflict Detection Rules


| **Same artifact_id, newer version** | AUTO OVERWRITE — write new version, increment version number, set superseded_by on old record. Keep full history. No HITL needed. |
| --- | --- |
| **Different artifact_id, same name AND same brand/domain/feature** | FLAG AS POTENTIAL DUPLICATE — sub-agent compares metadata and content summary. If confident they are the same artifact — recommend merge. HITL to confirm merge or keep both. |
| **Same name, different brand OR different feature** | NOT A CONFLICT — different artifacts sharing a name. Both kept. Registry differentiates by artifact_id and metadata. |
| **New artifact confidence LOWER than existing** | NEVER AUTO OVERWRITE — always HITL. Lower confidence artifact cannot silently replace higher confidence one. |
| **Derived artifact conflicts with its source** | FLAG — if a test_cases artifact derived from a journey_map contradicts the journey_map, surface as conflict with both sides. HITL to resolve. |
| **Same artifact_id, same version, different content** | FLAG AS CONFLICT — should not happen. Log as data integrity issue. HITL to resolve. Both versions quarantined until decision. |
## 6.2  Conflict Resolver Sub-Agent
The conflict resolver is a lightweight sub-agent that runs as part of KB Store ingestion. It has access to the registry and the incoming artifact metadata. It applies the rules above, makes an autonomous decision where possible, and produces a HITL package where not.

| **House Rules — Conflict Resolver**1. Never silently overwrite without logging the decision in the registry2. Always prefer the higher confidence artifact when confidence differs3. Never merge without HITL confirmation — merging is irreversible4. When in doubt — keep both, flag the conflict, surface to HITL5. Every conflict decision gets logged in the registry with rationale and timestamp |
| --- |
# 7. Domain Config — Client Agnostic Design
---The KB layer is client-agnostic by design. What changes between clients is the domain context — the business vocabulary, the brands, the domains, the known entities. This context is fed via a domain config JSON file. The infrastructure does not change.
## 7.1  Domain Config Structure
The domain config is plain English input from whoever knows the domain — an architect, a BA, a product owner. The LLM reads it and generates the ontology seed used by LightRAG for entity extraction. If nothing is known — LightRAG discovers on its own. If something is known — it follows the guidance.

| **Domain Config Schema**`client_name: Value Enterprise``description: <plain English — what this client does>``brands: [StraightTalk, TotalWireless, TracFone, WFM]``domains: [service_ordering, payments, identity, catalog, provisioning]``legacy_tech: [Java, Spring, Oracle DB, SOAP APIs]``nsa_tech: [NSA Platform, REST APIs, Event-driven]``known_entities: [ServiceOrder, Customer, Plan, Payment, Device]``known_rules: <any baseline business rules known upfront>``shared_elements: <concepts that apply across all brands>` |
| --- |
For an external or open source repo — domain config can be minimal or even auto-generated from the repo README. For a new client — an architect writes a few paragraphs in plain English and that becomes the domain config. LightRAG takes it from there.

# 8. Confluence Design
---## 8.1  Page Hierarchy


| `  Confluence Space: SDLC Knowledge Base``  │``  ├── StraightTalk                           (Brand page)``  │   ├── Service Ordering                   (Domain page)``  │   │   ├── Activation                     (Feature page — TOC of all artifacts)``  │   │   │   ├── Journey Map v1             (Artifact page)``  │   │   │   ├── Business Rules v1          (Artifact page)``  │   │   │   ├── Gap Analysis v1            (Artifact page)``  │   │   │   ├── BRD Final v1               (Artifact page)``  │   │   │   └── Test Cases v1              (Artifact page)``  │   │   └── PortIn                         (Feature page)``  │   └── Payments                           (Domain page)``  ├── TotalWireless                          (Brand page)``  ├── SHARED                                 (Shared elements page)``  └── EXT                                    (External repos page)` |
| --- |
## 8.2  Feature Page — TOC Design
Each feature page acts as a table of contents for all artifacts under that feature. Automatically generated and updated by the KB Store component every time a new artifact is ingested.

| **Feature Page Structure****Feature: Activation  |  Brand: StraightTalk  |  Domain: Service Ordering****Artifacts in this Feature:**📄 Journey Map v1  →  [link]  |  Producer: BRD Agent  |  Confidence: HIGH  |  Created: 2026-05-11📄 Business Rules v1  →  [link]  |  Producer: BRD Agent  |  Confidence: MEDIUM  |  Created: 2026-05-11📄 Gap Analysis v1  →  [link]  |  Producer: BRD Agent  |  Confidence: MEDIUM  |  Created: 2026-05-11📄 Test Cases v1  →  [link]  |  Producer: QA Agent  |  Confidence: HIGH  |  Created: 2026-05-12*Derived Artifacts: BRD Final derived from Journey Map + Business Rules + Gap Analysis* |
| --- |
# 9. Hypergraph — Navigation Layer
---The hypergraph is the navigation intelligence that sits between intent recognition and vector retrieval. It is not a document store and not an entity graph. It is a feature-level grouping structure — like a folder system for the knowledge base — that tells the RAG layer which artifacts to search before searching anything.

Think of it as: instead of searching all files on your laptop for tax information, you go to the taxes folder first. The hypergraph is that folder structure — but intelligent, self-updating, and cross-linked.

| **The hypergraph answers: WHICH artifacts? The vector store answers: WHAT within those artifacts?** |
| :---: |
## 9.1  Storage Backend — Decision & Upgrade Path


| **POC Storage****Decision:** JSON file — KB/graph/hypergraph.json**Why:** *Zero dependency. Human readable. Git-versionable. Easy to inspect and debug. Will hit limits at enterprise scale but perfect for proving the concept.* |
| --- |


| **Production Storage****Decision:** SQLite — KB/graph/hypergraph.db**Why:** *Same stack as registry. Handles concurrent writes. Indexed for fast alias lookup. No new dependency. Scales to millions of nodes comfortably. Query with SQL.* |
| --- |


| **Enterprise Storage****Decision:** Kuzu — embedded graph DB with Cypher query language**Why:** *True graph DB, embedded like SQLite, no server needed. Handles billions of nodes. Purpose-built for analytical graph workloads. pip install kuzu. Upgrade when SQLite lookup latency becomes a concern.* |
| --- |
Why not Neo4j: additional server cost, Docker dependency, operations overhead. We are not storing documents in the graph — only navigation metadata. The query pattern is simple lookup not complex traversal. Neo4j is the right answer only if we need graph visualization or multi-hop traversal at scale. Add it to the roadmap, not the current design.
## 9.2  Hypergraph Schema
The hypergraph has four components: nodes, hyperedges, alias index, and temp nodes. Every component is designed to be storage-backend-agnostic — same schema whether stored in JSON, SQLite, or Kuzu.
### Nodes — Feature-Level Groupings


| **node_id** | Unique identifier — e.g. node_ST_SO_Activation |
| --- | --- |
| **label** | Human-readable label — StraightTalk Service Ordering Activation |
| **brand** | ST | TW | TF | WFM | SHARED | EXT | VALUE |
| **domain** | service_ordering | payments | identity | catalog | etc. |
| **feature** | Activation | PortIn | Subscription | etc. |
| **artifact_ids** | List of artifact UUIDs that belong to this node — ALL types: journey_map, business_rules, test_cases, brd_final etc. |
| **aliases** | Natural language terms that map to this node — auto-generated by LLM from artifact content. e.g. activation flow, new service activation, onboarding |
| **confidence** | HIGH | MEDIUM | LOW — how confident the placement agent was about this grouping |
| **status** | ACTIVE | TEMP | MERGED | DEPRECATED |
| **is_temp** | Boolean — true for nodes the placement agent could not confidently classify. Pending human review. |
| **created_at** | UTC timestamp |
| **last_updated** | UTC timestamp |
| **created_by** | placement_agent | human |
| **human_reviewed** | Boolean — has a human confirmed this placement |
### Hyperedges — Cross-Node Connections
A hyperedge connects multiple nodes. It represents a concept or flow that spans features, domains, or brands. One hyperedge can connect any number of nodes — this is what makes it a hypergraph not a simple graph.

| **edge_id** | Unique identifier — e.g. edge_SO_domain |
| --- | --- |
| **label** | Human-readable label — Service Ordering Domain |
| **edge_type** | SAME_DOMAIN | SAME_CONCEPT_DIFFERENT_BRAND | SHARED_FLOW | CROSS_FEATURE | MANUAL |
| **connects_nodes** | List of node_ids this edge connects — can be any number |
| **aliases** | Terms that map to this edge — order management, service order, ordering flow |
| **similarity_score** | 0.0-1.0 — how similar are the connected nodes (from LLM analysis) |
| **differences** | List of known differences between connected nodes — e.g. TW uses different payment gateway |
| **created_by** | placement_agent | human |
| **human_reviewed** | Boolean |
| **created_at** | UTC timestamp |
### Alias Index — Fast Lookup Table
The alias index is the entry point for RAG queries. It maps natural language terms and business concepts to node_ids and edge_ids. Built automatically by the placement agent from artifact content and domain config. Humans can add more aliases manually.

| **alias_term** | Natural language term — order management | activation | taxes | subscription payment |
| --- | --- |
| **maps_to_nodes** | List of node_ids this term points to |
| **maps_to_edges** | List of edge_ids this term points to |
| **confidence** | How confident the alias assignment is |
| **source** | llm_generated | human_added | domain_config |
### Temp Nodes — Placement Pending Human Review
When the placement agent cannot confidently classify an artifact, it creates a TEMP node. The artifact is stored and accessible. A notification is written to notifications.json. The pipeline continues without blocking. A human reviews temp nodes async and either promotes them to permanent nodes or merges them with existing ones.

| **temp_node_id** | UUID prefixed with TEMP_ — e.g. TEMP_20260513_a3f9bc12 |
| --- | --- |
| **artifact_ids** | Artifacts placed here pending classification |
| **placement_context** | Full context the placement agent had — why it could not decide |
| **candidate_nodes** | List of existing nodes the agent considered — with similarity scores |
| **notification_sent** | Boolean — has notification been written to notifications.json |
| **created_at** | UTC timestamp |
### Full Hypergraph JSON Example


| `  {``    "hypergraph_version": "1.0",``    "last_updated": "2026-05-13T00:00:00Z",``    "nodes": {``      "node_ST_SO_Activation": {``        "node_id": "node_ST_SO_Activation",``        "label": "StraightTalk Service Ordering Activation",``        "brand": "ST",``        "domain": "service_ordering",``        "feature": "Activation",``        "artifact_ids": ["20260511_abc123", "20260511_def456", "20260512_ghi789"],``        "aliases": ["activation flow", "new activation", "service activation"],``        "confidence": "HIGH",``        "status": "ACTIVE",``        "is_temp": false,``        "human_reviewed": true``      },``      "node_TW_SO_Activation": {``        "node_id": "node_TW_SO_Activation",``        "label": "TotalWireless Service Ordering Activation",``        "brand": "TW",``        "domain": "service_ordering",``        "feature": "Activation",``        "artifact_ids": ["20260512_mno345"],``        "aliases": ["TW activation", "total wireless activation"],``        "confidence": "MEDIUM",``        "status": "ACTIVE"``      },``      "TEMP_20260513_xyz999": {``        "node_id": "TEMP_20260513_xyz999",``        "is_temp": true,``        "artifact_ids": ["20260513_pqr789"],``        "placement_context": "Artifact covers both PortIn and Activation — unclear boundary",``        "candidate_nodes": ["node_ST_SO_Activation", "node_ST_SO_PortIn"]``      }``    },``    "hyperedges": {``      "edge_SO_domain": {``        "edge_id": "edge_SO_domain",``        "label": "Service Ordering — All Brands",``        "edge_type": "SAME_DOMAIN",``        "connects_nodes": ["node_ST_SO_Activation", "node_TW_SO_Activation",``                           "node_ST_SO_PortIn"],``        "aliases": ["order management", "service order", "ordering", "activate"]``      },``      "edge_ST_TW_Activation_crossbrand": {``        "edge_id": "edge_ST_TW_Activation_crossbrand",``        "label": "Activation — Cross Brand Equivalent",``        "edge_type": "SAME_CONCEPT_DIFFERENT_BRAND",``        "connects_nodes": ["node_ST_SO_Activation", "node_TW_SO_Activation"],``        "similarity_score": 0.87,``        "differences": ["TW uses different payment gateway", "ST has loyalty points step"],``        "human_reviewed": false``      }``    },``    "alias_index": {``      "order management":    {"nodes": ["node_ST_SO_Activation"], "edges": ["edge_SO_domain"]},``      "activation":          {"nodes": ["node_ST_SO_Activation", "node_TW_SO_Activation"], "edges": []},``      "TW activation":       {"nodes": ["node_TW_SO_Activation"], "edges": []}``    }``  }` |
| --- |
# 10. Hypergraph Placement Agent
---

| **The placement agent is the intelligence that builds the hypergraph.***Not pattern matching. Not rule-based. Full LLM reasoning with complete artifact context — the same context the BRD agent had when it produced the artifact.* |
| :---: |
When an artifact arrives at KB Store, the placement agent receives the artifact content AND the full context the producing agent had — component name, domain, brand, what journeys were found, what rules were extracted, what the BRD says. It makes an intelligent placement decision. Not a simple field match.

This is the living memory of the enterprise. Getting placement right matters. A misplaced node corrupts the navigation layer and makes future retrieval imprecise. The placement agent is thorough, cautious, and never silently makes a bad decision.
## 10.1  The Five Placement Decisions


| **Decision 1 — PLACE IN EXISTING NODE**Condition: Artifact clearly belongs to an existing node. High semantic similarity. Same brand, domain, feature confirmed.Action: Append artifact UUID to existing node's artifact_ids list. Update node's aliases if new terms found in content.**Confidence required: HIGH. Notification: None. Pipeline: continues.** |
| --- |


| **Decision 2 — CREATE NEW NODE**Condition: Artifact covers a feature or topic not yet in the hypergraph. No existing node matches.Action: Create new permanent node. Populate from artifact content and producing agent context. Generate aliases from LLM. Check if a new hyperedge should connect this node to an existing domain or brand group.**Confidence required: HIGH. Notification: None. Pipeline: continues.** |
| --- |


| **Decision 3 — CREATE NEW HYPEREDGE**Condition: Artifact spans multiple existing nodes — it connects concepts across features, brands, or domains. A bridge artifact.Action: Place artifact in the most relevant node. Create a hyperedge connecting the related nodes. Describe differences between connected nodes. Set human_reviewed: false.**Confidence required: MEDIUM. Notification: Written to notifications.json for async review. Pipeline: continues.** |
| --- |


| **Decision 4 — AMBIGUOUS — TEMP NODE + NOTIFICATION**Condition: Cannot determine placement confidently. Multiple candidate nodes with similar scores. Artifact spans unclear boundaries.Action: Create TEMP node with full placement context preserved. Write notification to notifications.json. Artifact is accessible but isolated until human reviews. Never blocks the pipeline.**Confidence: LOW. Notification: Yes — async, non-blocking. Pipeline: continues immediately.** |
| --- |


| **Decision 5 — MERGE PROPOSAL**Condition: New artifact appears to cover the same concept as an existing node but from a different angle — possibly the same feature with more detail, or a cross-brand equivalent.Action: Place artifact in BOTH candidate nodes temporarily. Write merge proposal to notifications.json with evidence for merge and evidence against. Human confirms or rejects. If confirmed — merge nodes, redirect all artifact_ids. If rejected — leave in both.**Confidence: MEDIUM. Notification: Yes — merge proposal. Pipeline: continues. Human reviews async.** |
| --- |
## 10.2  The Notification System — Async, Non-Blocking
The placement agent never blocks the pipeline. Every decision that needs human review gets written to notifications.json as an async notification. A developer or architect reviews the file daily or weekly — not in real time. The pipeline keeps running.

| `  notifications.json structure:``  {``    "notifications": [``      {``        "notification_id": "notif_20260513_001",``        "type": "TEMP_NODE_REVIEW | MERGE_PROPOSAL | NEW_HYPEREDGE_REVIEW",``        "priority": "LOW | MEDIUM | HIGH",``        "created_at": "2026-05-13T00:00:00Z",``        "status": "PENDING | REVIEWED | RESOLVED",``        "artifact_id": "20260513_xyz999",``        "artifact_name": "ST_SO_Activation_journey_map_v1.json",``        "placement_context": "Full reasoning from placement agent",``        "candidate_nodes": [``          {"node_id": "node_ST_SO_Activation", "similarity": 0.72},``          {"node_id": "node_ST_SO_PortIn", "similarity": 0.68}``        ],``        "recommended_action": "Review and assign to node_ST_SO_Activation",``        "human_decision": "",   // human fills this in``        "resolved_at": ""``      }``    ]``  }` |
| --- |
## 10.3  Confluence Mirrors the Hypergraph
The Confluence space structure is automatically kept in sync with the hypergraph. Every time a node is created or updated — the corresponding Confluence page is created or updated. The folder structure in KB and the page hierarchy in Confluence are always in sync. One source of truth drives both.

| `  Hypergraph Node: node_ST_SO_Activation``       ↓  automatically creates/updates``  Confluence: SDLC KB / StraightTalk / ServiceOrdering / Activation``       with TOC listing all artifact UUIDs and links``  Hyperedge: edge_SO_domain (connects ST + TW activation nodes)``       ↓  automatically creates/updates``  Confluence: SDLC KB / SHARED / ServiceOrdering / cross_brand_index page``       with links to both ST and TW Activation pages``  TEMP node created``       ↓  automatically creates``  Confluence: SDLC KB / PENDING_REVIEW / TEMP_20260513_xyz999``       clearly labeled as pending human classification` |
| --- |


| **Graph + Vector Framework****Decision:** LightRAG**Why:** *Open source, pip installable, zero cost, zero external dependency. Native two-hop retrieval — graph for navigation, vector store for content. Swappable vector backend. Adaptive entity extraction via custom prompts. Closest available tool to our designed architecture.* |
| --- |
## 9.1  How LightRAG Works In This Design
LightRAG operates in two phases — ingestion and retrieval. Both are handled by the RAG component, which builds on top of the JSON files the KB Store produces.

| **Ingestion Phase** | KB Store writes JSON artifact. RAG component reads it. Sends content to LightRAG with domain config as ontology prompt. LightRAG extracts entities and relationships using Claude. Stores entity graph (graphml). Chunks and embeds content. Stores in vector backend. Entity tags written back to artifact metadata. |
| --- | --- |
| **Retrieval Phase** | Query arrives. LightRAG builds context subgraph — finds relevant entities in graph, identifies which artifact nodes they belong to. Returns targeted artifact list. Vector search runs ONLY within those artifact embeddings. Answer assembled from targeted chunks. Write-back payload returned with answer. |
| **Ontology Guidance** | Domain config JSON passed as system prompt context to LightRAG entity extraction. LightRAG follows the known entity types as guidance. Discovers new entities beyond the seed. Evolves ontology over time as more artifacts are ingested. |
| **Write-back** | After query is answered — kb_writeback() function called with: artifact_ids used, query intent label, usefulness flag, task type helped. One function, no extra LLM call. Metadata updated in SQLite registry and LightRAG graph node properties. |
## 9.2  Vector Store & Embeddings


| **Vector Store — POC****Decision:** ChromaDB (local, persistent)**Why:** *Zero infrastructure, pip install, persistent to disk, good enough for POC scale. Already in the BRD Agent POC stack. Consistent choice.* |
| --- |


| **Vector Store — Production (Option)****Decision:** LanceDB or Weaviate**Why:** *LanceDB: lightweight, local-first, scales well, native LightRAG integration. Weaviate: full-featured, cloud-native, good for enterprise scale. Decision deferred to production phase based on scale requirements.* |
| --- |


| **Embeddings Model****Decision:** sentence-transformers / all-MiniLM-L6-v2 for POC**Why:** *Local, no API cost, fast, good quality for semantic similarity. Already in BRD Agent POC requirements.txt. For production — OpenAI text-embedding-3-small or Anthropic embeddings if cost-quality tradeoff warrants it.* |
| --- |
## 9.3  Session Context
Within an active RAG session — same agent or human asking multiple questions — conversation history is maintained in a session object. Each query is informed by prior queries and retrieved artifacts in the session. Session cleared when the interaction ends. Enables coherent multi-turn interactions for HITL decision support.

| **session_id** | UUID generated at session start |
| --- | --- |
| **started_at** | UTC timestamp |
| **queries** | List of all queries in this session with timestamps |
| **retrieved_artifacts** | All artifact IDs retrieved during this session — deduped |
| **context_summary** | Rolling LLM-generated summary of what has been discussed — used to inform subsequent queries without re-sending full history |
| **agent_or_human** | Who initiated the session — agent name or human identifier |
# 11. LightRAG Design — RAG Component
---

| **Graph + Vector Framework****Decision:** LightRAG**Why:** *Open source, pip installable, zero cost, zero external dependency. Native two-hop retrieval — entity graph for within-document navigation, vector store for chunk retrieval. Swappable vector backend. Adaptive entity extraction via custom prompts. Works WITH our hypergraph — hypergraph handles document-group navigation, LightRAG handles within-document intelligence.* |
| --- |
## 13.1  How LightRAG Fits In This Design
LightRAG does NOT replace the hypergraph. They work at different levels. The hypergraph navigates to the right group of documents. LightRAG then works within those documents to find the precise answer.

| **Hypergraph job** | Which documents? — navigate to the right feature/domain/brand group, return UUID list |
| --- | --- |
| **LightRAG job** | What within those documents? — entity graph + vector search within the targeted UUID set |
| **Together** | High precision retrieval — right folder first, then right answer within that folder |
| **Separately (fallback)** | LightRAG alone = brute force RAG = LOW confidence label |
## 11.2  Vector Store & Embeddings


| **Vector Store — POC****Decision:** ChromaDB (local, persistent)**Why:** *Zero infrastructure, pip install, persistent to disk, already in BRD Agent POC stack.* |
| --- |


| **Vector Store — Production****Decision:** LanceDB or Weaviate**Why:** *LanceDB: lightweight, local-first, native LightRAG integration. Weaviate: full-featured, enterprise scale. Decision deferred to scale assessment.* |
| --- |


| **Embeddings — POC****Decision:** sentence-transformers / all-MiniLM-L6-v2**Why:** *Local, no API cost, fast, good semantic similarity. Already in BRD Agent POC requirements.* |
| --- |
# 12. Technology Stack — Decisions & Rationale
---

| **Artifact Registry — POC** | JSON file (artifact_registry.json) — if developer chooses. Ask in setup: is SQLite available? If yes use SQLite. If no use JSON. |
| --- | --- |
| **Artifact Registry — Production** | SQLite (artifact_registry.db) — concurrent writes, indexed, human-inspectable |
| **Hypergraph Storage — POC** | JSON file (hypergraph.json) — zero dependency, human readable, git-versionable |
| **Hypergraph Storage — Production** | SQLite (hypergraph.db) — same stack as registry, indexed alias lookup, concurrent writes |
| **Hypergraph Storage — Enterprise** | Kuzu — embedded graph DB, Cypher queries, billions of nodes, no server needed |
| **Why not Neo4j** | Additional server cost, Docker dependency, operations overhead. Not storing documents in graph — only navigation metadata. Simple lookup pattern does not need graph traversal engine. |
| **Document Store** | JSON files in structured folder hierarchy — mirrors hypergraph structure |
| **Human Layer** | Confluence via REST API — auto page creation, TOC, mirrors hypergraph structure exactly |
| **Graph + RAG Framework** | LightRAG — open source, local, adaptive ontology via prompt. Works within artifact sets identified by hypergraph. |
| **Vector Store — POC** | ChromaDB — local persistent, zero infra |
| **Vector Store — Production** | LanceDB or Weaviate — decision deferred to scale assessment |
| **Embeddings — POC** | sentence-transformers / all-MiniLM-L6-v2 — local, no API cost |
| **Embeddings — Production** | OpenAI text-embedding-3-small or Anthropic embeddings — evaluate at production stage |
| **LLM — Placement Agent** | Claude Haiku — intelligent placement decisions, lightweight per artifact |
| **LLM — Metadata Extraction** | Claude Haiku — structured extraction from artifact content |
| **LLM — Alias Generation** | Claude Haiku — generate natural language aliases from artifact content + domain config |
| **LLM — Intent Recognition (POC)** | Claude Sonnet — classify query intent and extract keywords before hypergraph lookup |
| **LLM — Intent Recognition (Production)** | Sentence-transformers cosine similarity against FAQ cache query embeddings — replaces LLM call for repeat queries. No model training needed. |
| **Knowledge Orchestrator Agent (Phase 2)** | New component wrapping RAG layer. Caller identification, metadata-first retrieval, context graph construction, role-aware answer composition. Claude Sonnet for orchestration reasoning. |
| **Conversation Write-Back (Phase 2)** | Session-level metadata enrichment at conversation end. Outcome-confirmed signals, gap backlog, session_artifact to registry. |
| **Gap Backlog (Phase 2)** | Queryable list of questions KB could not answer — feeds BRD Agent run planning. KB diagnoses its own knowledge gaps. |
| **Query Log (POC)** | query_log.json — every RAG query logged as seed data for Phase 2 FAQ cache |
| **Concurrent Registry Writes** | SQLite WAL mode — handles parallel agent writes natively |
| **Confluence Sync** | Confluence REST API — Python atlassian-python-api library |
| **Notification System** | notifications.json — async, non-blocking, human reviews periodically |
| **Artifact ID Generation** | Python uuid4 + datetime UTC — timestamp_uuid format, sortable, timezone-safe |
| **KB Store Trigger** | Auto: post-agent pipeline hook. Manual: python kb_store.py --path |
Green = decided and locked. Amber = decided for POC but option exists to upgrade for production. All amber decisions are documented with the upgrade path above.

# 13. Write-Back Loop 
---## 13.1  Write-Back Function
kb_writeback() is a lightweight function called after every RAG query is answered. The LLM that handled the query returns both the answer and the write-back payload in a single call — no additional LLM invocation needed.

| **kb_writeback() Signature**`kb_writeback(``    artifact_ids: list[str],      # artifacts that helped``    query_intent: str,             # classified intent label``    task_type: str,                # what was being done``    was_useful: bool,              # did this artifact help``    session_id: str,               # session context``    hitl_decision_id: str = None   # if this supported a HITL decision``)` |
| --- |
## 13.2  Phase 2 — FAQ Cache for Cost Reduction


| **Phase 2 — Not part of POC. Design captured here for future production implementation.** |
| :---: |
Every RAG query costs LLM tokens. At enterprise scale — dozens of agents querying continuously — this becomes significant. The FAQ cache reduces repeat RAG costs to near-zero without replacing RAG or requiring model training.

The insight: many queries in an enterprise system are similar or identical. 'How does activation work?' gets asked by a BRD agent, a QA agent, a developer, an architect. If the source documents have not changed — the answer is the same. Store it once, serve it many times.
### How It Works


| `  New query arrives``       |``       v``  Lightweight intent model — embed query``  Cosine similarity search against cached query embeddings``       |``       +── Similarity > 0.92 AND source docs UNCHANGED``       |       → Return cached answer directly``       |       → No RAG, no LLM, near-zero cost, instant``       |``       +── Similarity 0.75-0.92 OR source docs CHANGED``       |       → Use cached answer as context``       |       → Run targeted RAG to verify/update``       |       → Update cache with fresh answer``       |``       +── Similarity < 0.75 — new query never seen``               → Full RAG pipeline``               → Store query + answer + source UUIDs in FAQ cache``               → Next similar query hits cache` |
| --- |
### FAQ Cache Storage


| **Location** | KB/cache/faq_cache.db (SQLite) + KB/cache/faq_cache_index/ (ChromaDB for query embeddings) |
| --- | --- |
| **SQLite stores** | query_text, answer, source_artifact_ids[], source_artifact_versions{}, created_at, last_validated, access_count, was_useful, staleness_flag |
| **ChromaDB stores** | query embeddings only — for fast cosine similarity search on new incoming queries |
| **Cache invalidation trigger** | KB Store detects artifact update → checks faq_cache for entries referencing that artifact UUID → marks STALE. Cost: one SQL query per artifact update. Zero overhead. |
| **Similarity threshold** | Tunable in config. Start at 0.92 for high-confidence cache hits. Lower to 0.85 as cache matures and proves reliable. |
| **Intent model** | sentence-transformers cosine similarity against stored query embeddings. No training. No retraining cycles. Works from day one. |
| **Why not SVM** | SVM classifies intent but does not eliminate RAG calls — you still have to do RAG after classification. FAQ cache eliminates the RAG call entirely for repeat queries. The effort of building and maintaining an SVM model saves one LLM call per query while adding MLOps complexity. FAQ cache saves the entire RAG pipeline for repeat queries with zero MLOps overhead. |
### Query Log — What We Store Now (POC)
In POC — we do not build the FAQ cache yet. But we store the raw material for it. Every RAG query is logged in the artifact registry metadata (query_intents field) and in a query_log.json file. When Phase 2 begins — this log becomes the seed for the FAQ cache. No data is lost.

| **query_log.json** | Stored in KB/cache/query_log.json — one entry per query |
| --- | --- |
| **Stores** | query_text, timestamp, source_artifact_ids, answer_summary, intent_label, session_id, was_useful |
| **Purpose** | Analytics, debugging, FAQ cache seed for Phase 2 |
| **Cost** | Near zero — a JSON append per query |
# 14. Lineage & Full Traceability
---Every artifact knows what it came from. The derived_from field in both the artifact registry and the artifact metadata creates a complete traceability chain from story to BRD to code to test to defect. This chain is stored in both places — registry for global lookup, metadata for artifact-level detail. Both are updated at the same time on every write.

| `  Story Brief (story_brief_v1)``        |``        | derived_from: []``        v``  BRD Final (brd_final_v1)    ← derived_from: [story_brief_v1]``        |``        +── Journey Map       ← derived_from: [brd_final_v1]``        +── Business Rules    ← derived_from: [brd_final_v1]``        +── AC Criteria       ← derived_from: [brd_final_v1]``        |``        v``  Test Cases (test_cases_v1)  ← derived_from: [ac_criteria_v1, journey_map_v1]``        |``        v``  Defect Analysis             ← derived_from: [test_cases_v1, business_rules_v1]``        |``        v``  Code Review                 ← derived_from: [brd_final_v1, ac_criteria_v1]``  Any artifact can be traced back to its origin.``  Any artifact can trace forward to what was built from it.` |
| --- |
# 15. Entry & Exit Criteria — KB Store Component
---## 15.1  Entry Criteria
- Agent has completed its run — output artifacts exist in a known folder path

- OR: Manual path provided via --path argument pointing to existing artifact folder

- Domain config JSON is available (can be empty for first-time unknown domain)

- SQLite registry is accessible — created automatically if it does not exist

- Confluence credentials are available if Confluence sync is enabled
## 13.2  Exit Criteria
- All artifacts in the input folder renamed per naming convention

- Metadata node created or updated in SQLite registry for every artifact

- Conflict resolution completed — autonomous decision or HITL package produced

- JSON files written to correct folder in KB hierarchy

- Confluence pages created or updated with artifact content and feature TOC refreshed

- artifact_registry.db updated with new entries and lineage links

- Ingestion log entry written with run summary — artifacts processed, conflicts found, errors
## 13.3  Key Design Decisions — Summary


| **KB Store as standalone component** | Agents do not know about KB. KB does not know about agents. Clean separation. KB consumes a path — that path can come from any agent or human. |
| --- | --- |
| **Why structured KB vs pure RAG dump** | Pure RAG works for under 200 documents. Enterprise scale with thousands of artifacts across brands, domains, migrations, and new development needs precision navigation. Hypergraph gives targeted retrieval — go to the right folder before searching. Reduces noise, cost, and latency by orders of magnitude. |
| **Hypergraph as navigation layer** | Not entity-level graph. Not document store. Feature-group navigation — which documents to search, not what is inside them. LightRAG handles within-document intelligence. Hypergraph handles document-group navigation. They complement each other. |
| **Hypergraph storage upgrade path** | JSON (POC, zero dependency) → SQLite (production, concurrent writes, indexed) → Kuzu (enterprise, true graph DB, Cypher). Same schema throughout. Config decides backend. Agent code never knows which one. |
| **Why not Neo4j** | Additional server cost, Docker dependency, operations overhead. Query pattern is simple lookup — go from alias to node to UUID list. SQL handles this cleanly. Neo4j reserved for future if graph visualization or complex multi-hop traversal is needed. |
| **Intelligent placement agent** | Not pattern matching. Full LLM reasoning with complete producing-agent context. Five decisions: place in existing, create new node, create hyperedge, TEMP node, merge proposal. Never blocks pipeline. Async notifications for human review. |
| **Confluence mirrors hypergraph** | One source of truth — hypergraph structure drives both machine navigation and human navigation. When a node is created, the Confluence page is created. Same hierarchy. Human and machine always see the same structure. |
| **Registry choice is configurable** | Developer asked at setup: is SQLite available? If yes — SQLite for both registry and hypergraph. If no — JSON for both. Same interface, different adapter. Config flag, no code change. |
| **Two trigger modes in one component** | Auto: fires after agent. Manual: --path argument. Same code, same logic. |
| **Alias index LLM-generated** | Aliases generated from artifact content and domain config by LLM at ingestion time. Humans can add more manually. The alias index is what makes natural language queries work without exact keyword matching. |
| **Brute force fallback** | If hypergraph navigation finds nothing — fall through to standard RAG on all embeddings. Return answer with LOW confidence label. Transparent to user about confidence level. |
| **Lineage in both registry and hypergraph** | Full traceability from story to defect. derived_from tracked in registry metadata. Hypergraph edges capture cross-artifact relationships. Both updated simultaneously. |
| **SVM training as side effect** | Every query intent stored in metadata. Labeled training data accumulates naturally. No separate labeling program needed. |


| **The hypergraph is the folder system. The vector store is the search engine. Together they give you precision at enterprise scale.**Build the folder system right first. Then the search engine knows where to look. |
| :---: |
# 16. Knowledge Orchestrator Agent
---

| **Phase 2 — Not part of POC. Design fully specified here. Implementation MD to be written separately.** |
| :---: |
The current RAG design is intelligent retrieval — it finds the right artifacts and extracts relevant chunks. But it serves the same answer to everyone regardless of who is asking or what they will do with it. The metadata we so carefully built — usefulness_scores, used_for, query_intents, confidence, derived_from, producer_agent — is used only for navigation, not for shaping the answer.

The Knowledge Orchestrator Agent closes this gap. It sits between the query interface and the RAG layer. It knows who is asking, what they are trying to do, and what the metadata says about the artifacts it is about to serve. It composes a response that is tailored to the consumer — not just retrieved for them.

This is the Chef Agent from the original Knowledge Layer design — now fully specified for implementation.



| Current: Query → RAG → Same answer for everyone**Phase 2: Query → Knowledge Orchestrator → Role-aware answer shaped by metadata intelligence** |
| :---: |
## 16.1  The Five Components
### Component 1 — Caller Identification
Before retrieving anything — the orchestrator identifies who is asking and in what context. This determines everything about how knowledge is composed and presented.

| **who_is_asking** | Agent type (BRD agent, QA agent, dev agent, defect triage agent) or human role (BA, architect, engineer, product owner) |
| --- | --- |
| **what_is_the_task** | What they are trying to accomplish — write a BRD section, fix a defect, generate test cases, make an architecture decision |
| **what_is_the_occasion** | The SDLC phase — requirements, design, development, testing, maintenance, incident response |
| **what_is_the_appetite** | How deep they need to go — summary (headlines only), standard (key details), deep (full context), surgical (one specific answer) |
| **what_boundaries_apply** | Domain, brand, regulatory context — derived from caller identity and query content |
### Component 2 — Metadata-First Retrieval
The orchestrator queries the registry BEFORE touching the vector store. This is the key innovation — metadata filtering narrows the candidate artifact set so that RAG operates on a pre-qualified, role-relevant set of documents.

| **Role-based ranking** | Filter artifacts by used_for matching this caller's task type. Rank by usefulness_scores for this specific task. A QA agent gets artifacts with high test_case_writing scores first. |
| --- | --- |
| **Confidence filtering** | Apply confidence threshold appropriate for the occasion. Architecture decisions need HIGH confidence artifacts. Quick summaries can tolerate MEDIUM. |
| **Lineage tracing** | Follow derived_from chains relevant to the question. If asking about test cases — surface the ACs they were derived from AND the BRD those ACs came from. Full lineage as context. |
| **Freshness check** | Check last_accessed and updated_at. Flag if artifact has not been validated recently. Do not silently serve stale knowledge. |
| **Cross-brand relevance** | Check cross_brand_relevance field. If asking about TW activation and ST activation artifacts have been marked relevant — surface them with cross-brand note. |
| **Entity alignment** | Match entity_tags against query entities. Prefer artifacts whose tagged entities overlap with what the query is about. |
### Component 3 — Context Graph Construction
Before calling LightRAG — the orchestrator builds a context package from metadata alone. This is the Chef composing the meal before serving. The context package shapes how LightRAG retrieves and how the LLM answers.

| `  Context Package built from metadata:``  {``    "caller_role": "QA Engineer",``    "occasion": "writing test cases for activation flow",``    "appetite": "deep",``    "ranked_artifacts": [``      {"name": "ST_SO_Activation_ac_criteria_v1.json",``       "usefulness_score": 0.94,  <- high for test_case_writing``       "confidence": "HIGH",``       "derived_from": ["brd_final_v1"]},``      {"name": "ST_SO_Activation_journey_map_v1.json",``       "usefulness_score": 0.87,``       "confidence": "HIGH"}``    ],``    "lineage_context": "ACs derived from BRD v1 which locked 2026-05-11",``    "confidence_flags": [],``    "cross_brand_notes": "TW has similar activation — see edge_ST_TW_Activation",``    "present_as": "Given/When/Then format preferred for QA",``    "caveats": []``  }` |
| --- |
### Component 4 — Role-Aware RAG
The context package is passed to LightRAG alongside the query. LightRAG searches within the pre-qualified ranked artifact set. The LLM composes the answer using both the retrieved chunks AND the metadata context — shaping the response format and emphasis for the specific consumer.

| **BRD Agent receives** | Journeys first, business rules second, gaps third. Structured for BRD section writing. Confidence explicitly stated per finding. |
| --- | --- |
| **Dev Agent receives** | Business rules with NSA mapping, ACs as implementation targets, gap analysis with transformation logic. Technical format, actionable. |
| **QA Agent receives** | Test cases, ACs in Given/When/Then, regression gaps flagged. Test-case-ready format. Edge cases surfaced prominently. |
| **Architect receives** | Dependencies, risks, gap analysis, NSA capability notes. System-level view. Known limitations highlighted. |
| **Human BA receives** | Plain English summary, confidence labels visible, source artifact links, lineage mentioned. Readable, not technical. |
| **Maintenance Agent receives** | Full lineage from creation to present, decision history, version trail, who confirmed what and when. Forensic view. |
### Component 5 — Conversation-Level Write-Back
Current write-back happens per query. The orchestrator adds conversation-level write-back — richer learning accumulated across an entire interaction and written back at session end.

| **Per-query write-back (current)** | After each query: update used_for, query_intents, access_count, usefulness_scores on retrieved artifacts. Already implemented in Phase 1. |
| --- | --- |
| **Per-conversation write-back (new)** | At session end: write back what the CONVERSATION revealed — which artifacts stayed relevant across multiple turns, what follow-up questions emerged, what the consumer ultimately did with the knowledge. |
| **Conversation signals** | If an artifact was retrieved in turn 1 and the human asked 3 follow-up questions about it — that is a strong usefulness signal stronger than a single query hit. Record it. |
| **Gap signals** | Questions the KB could not answer become gap_signals on the session. These feed the knowledge acquisition backlog — what we need to generate BRD artifacts for next. |
| **Role refinement** | As the conversation develops, the orchestrator learns more about the caller. A human who asks progressively deeper technical questions is probably an architect not a BA. Update role inference for future sessions. |
| **Session metadata** | Full session written to registry as a session_artifact — query sequence, artifacts used, gaps identified, role inferred, outcomes. Queryable later for analytics. |
## 16.2  Session Context — What Gets Maintained
The orchestrator maintains a rich session context across all turns of a conversation. This is more than just conversation history — it is a growing understanding of the caller, their needs, and what the KB has and has not been able to serve.

| `  Session Context Object (maintained across all turns):``  {``    session_id``    caller_role              // refined turn by turn``    occasion``    appetite``    // Turn history``    turns: [``      {query, intent, artifacts_used, answer_confidence, was_useful}``    ]``    // Accumulated artifact intelligence``    artifacts_referenced: {``      artifact_id: {``        times_referenced: int,``        usefulness_per_turn: [bool],``        follow_up_questions_triggered: int  // strong usefulness signal``      }``    }``    // Knowledge gaps discovered this session``    gaps_identified: [``      {question_asked, confidence_returned, suggested_source}``    ]``    // Context summary for next turn``    rolling_summary: "string — what has been discussed"``    // Written back to registry at session end``    session_outcome: "wrote_brd_section|fixed_defect|wrote_tests|researched"``  }` |
| --- |
## 16.3  The Write-Back Enhancement — What Metadata Learns
With the Knowledge Orchestrator, metadata becomes genuinely intelligent over time. Each session teaches the system something new about its artifacts and its users.

| **From per-query write-back** | used_for list grows. query_intents accumulates labels. access_count increments. usefulness_scores per task type refined. |
| --- | --- |
| **From conversation write-back** | follow_up_signal: how many follow-up questions this artifact triggered — strong indicator of relevance and depth. Artifacts that anchor long conversations score higher than those referenced once. |
| **From session outcomes** | If a QA engineer's session ended with 'wrote_tests' and this artifact was central — its test_case_writing usefulness score gets a strong positive signal. Not just was_useful:true but outcome-confirmed. |
| **From gap signals** | Questions that returned NOT_FOUND are written to a gap_backlog. This tells the SDLC team which repos or components need BRD Agent to run on them. The KB diagnoses its own gaps. |
| **From role inference** | If 5 different sessions identified callers as QA engineers and all retrieved the same artifact — that artifact's used_for gets qa_primary_resource added. The system learns which artifacts are role-canonical. |
## 16.4  Knowledge Orchestrator — Full Flow Diagram


| `  Query arrives (from agent or human)``       |``       v``  [1] Caller Identification``       Who: agent DNA read OR human role inferred from query style``       Task: what are they trying to DO``       Occasion: which SDLC phase``       Appetite: summary / standard / deep / surgical``       |``       v``  [2] Metadata-First Retrieval (registry — no RAG yet)``       Filter: brand, domain, feature from intent``       Rank: by usefulness_scores for this caller's task type``       Trace: derived_from chains for lineage context``       Flag: low confidence, stale, cross-brand relevant``       Result: ranked candidate artifact list + metadata context``       |``       v``  [3] Context Graph Construction``       Build context package: ranked artifacts + metadata signals``       Format preference for this caller role``       Lineage notes, confidence caveats, cross-brand notes``       |``       v``  [4] Role-Aware RAG``       Pass: query + context package to LightRAG``       Search: within ranked artifact embeddings only``       Compose: answer shaped for caller role and appetite``       |``       +── Found (HIGH) → Role-shaped answer + sources + lineage``       +── Partial (LOW) → Answer + LOW confidence + caveat``       +── Not found → Honest not-found + gap_signal recorded``       |``       v``  [5] Return to caller``       Answer shaped for their role``       Confidence clearly labeled``       Source artifacts listed (for audit)``       Navigation path (which hypergraph node)``       |``       v``  [6] Per-Query Write-Back (immediate)``       Update artifact metadata: used_for, query_intents,``       access_count, usefulness_scores``       |``       v``  [7] Session Context Update``       Add turn to session history``       Update artifacts_referenced with follow-up signal``       Update rolling_summary``       |``  (session continues — context maintained across turns)``       |``  [8] Session End — Conversation Write-Back``       Write session_artifact to registry``       Apply outcome-confirmed usefulness signals``       Write gap_signals to gap_backlog``       Refine role inference for this caller` |
| --- |
## 16.5  Phase 2 MD File — What It Will Contain


| **Implementation MD for Phase 2 to be written after Phase 1 (KB Store + RAG POC) is running.** |
| :---: |
The Phase 2 MD assumes the KB Store + RAG POC (Phases 1-14) is fully operational. It adds the Knowledge Orchestrator Agent as a new component with the following phases:

| **Phase 15 — Caller Identification Module** | Detect caller role from agent DNA or infer from human query patterns. Build caller_profile object passed to all subsequent components. |
| --- | --- |
| **Phase 16 — Metadata-First Retrieval** | Registry query layer that runs before RAG. Filters by role-relevant artifact types. Ranks by usefulness_scores for the caller's task type. Traces derived_from chains. Returns ranked candidate list with metadata context. |
| **Phase 17 — Context Graph Constructor** | Builds the context package from metadata. Formats it for the caller's role and appetite. Adds lineage notes, confidence caveats, cross-brand signals. |
| **Phase 18 — Role-Aware RAG Integration** | Extends the existing query engine to accept context package. Shapes LightRAG retrieval by pre-qualified artifact set. Composes role-specific answer format. |
| **Phase 19 — Conversation Context Manager** | Extends session_manager to maintain full conversation-level context. Tracks artifacts referenced across turns. Accumulates follow-up signals. Maintains rolling_summary. |
| **Phase 20 — Conversation Write-Back** | End-of-session write-back. Applies outcome-confirmed signals to artifact metadata. Writes gap_signals to gap_backlog. Writes session_artifact to registry. |
| **Phase 21 — Gap Backlog** | A queryable list of questions the KB could not answer. Feeds the SDLC team's BRD Agent run planning. KB diagnoses its own knowledge gaps. |
| **Phase 22 — FAQ Cache** | SQLite + ChromaDB cache for repeat queries. Invalidates when source artifacts change. Near-zero cost for repeat queries. Seeded from query_log.json built in Phase 8. |
| **Phase 23 — Enhanced UI** | Update Streamlit UI to show role selection, appetite control, lineage visualization, gap backlog management. Update agent interface to pass caller_profile. |
## 16.6  Why Phase 2 — Not POC
The Knowledge Orchestrator can only be as good as the metadata it has to work with. In Phase 1 POC — metadata is sparse. Only a few components have been analyzed. usefulness_scores are empty. query_intents are empty. role inferences do not exist yet.

The orchestrator needs a warm KB to be intelligent. Running it on a cold KB produces mediocre results and wastes the design. Phase 1 POC exists precisely to warm the KB — accumulate metadata, populate usefulness_scores, build query_intents history. By the time Phase 2 is built, the KB has enough signal for the orchestrator to make genuinely intelligent decisions.

Build Phase 1 right. Run it. Let it accumulate. Then build the orchestrator on top of rich, meaningful metadata. That is when it becomes the veteran consultant it is designed to be.

# 17. Build Sequence
---## Phase 1 — POC (Current MD: KB_STORE_AND_RAG_POC.md)


| **Step 1 — KB Store Core** | Artifact receiver, renamer, metadata extractor, conflict resolver, JSON writer, registry. Foundation. |
| --- | --- |
| **Step 2 — Hypergraph Builder** | Placement agent, hypergraph schema, alias index, TEMP nodes, notifications. |
| **Step 3 — Confluence Sync** | Pages mirroring hypergraph structure, TOC generation. |
| **Step 4 — RAG Setup** | LightRAG initialization, bulk ingestion, embedding hook. |
| **Step 5 — Query Interface** | Intent recognition, hypergraph navigation, targeted vector search, confidence labels. |
| **Step 6 — UI Interfaces** | Agent Python function, optional REST API, Streamlit human UI. |
| **Step 7 — Write-back + Query Log** | Per-query write-back to artifact metadata. query_log.json for Phase 2 seeding. |
## Phase 2 — Production (MD to be written — see Section 16.5)


| **Step 8 — Knowledge Orchestrator** | Caller identification, metadata-first retrieval, context graph construction, role-aware RAG, conversation context manager. |
| --- | --- |
| **Step 9 — Conversation Write-Back** | Session-level write-back, outcome signals, gap backlog, session_artifact to registry. |
| **Step 10 — FAQ Cache** | SQLite + ChromaDB query cache seeded from query_log. Near-zero cost for repeat queries. |
| **Step 11 — Enhanced UI** | Role selection, appetite control, lineage visualization, gap backlog management. |
| **Step 12 — Production Deployment** | Docker packaging, persistent hosting, multi-user support, monitoring. |


| **Phase 1 builds the foundation. Phase 2 makes it intelligent.**The metadata is the intelligence. The orchestrator is what uses it. |
| :---: |

