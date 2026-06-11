# Decisions

## Decision: SQLite over Postgres

**Context:** DealRadar is a single-operator, cron-driven pipeline that needs to be trivially reproducible by anyone reviewing the project. Running a Postgres instance adds operational overhead — a server to provision, secure, back up, and connect to — for a workload that is low-volume and write-batched once per day.

**Decision:** Use SQLite as the entity store. The database is a single file on disk, with no server process to run.

**Consequences:** Zero ops — there is no database to manage, and cron remains the only moving part. Reviewers can clone the repo and run the pipeline end-to-end without standing up any infrastructure. The trade-off is limited concurrency and no horizontal scaling, both acceptable at v1 volumes; migrating to Postgres later is a contained change if throughput demands it.

## Decision: Cite-or-omit anti-hallucination

**Context:** The LLM enrichment step writes investment memos that partners may act on. A fabricated claim — a fake funding round, an invented founder background — is worse than a missing one, because it erodes trust in the entire digest.

**Decision:** Every claim in an LLM-generated memo must map to a cited evidence URL drawn from collected source data. If the model cannot cite a claim, the instruction is to omit it entirely rather than assert it.

**Consequences:** Hallucinations become structurally impossible to pass through to the reader — an uncited claim is dropped by construction, not by post-hoc filtering. Memos are more conservative and occasionally thinner, but every line is auditable back to a source. This also makes the output reviewable: a human can spot-check any claim by following its citation.

## Decision: Companies House before Product Hunt

**Context:** Collector build order determines how quickly the pipeline produces high-signal candidates. The available sources vary widely in precision and cost — some are noisy launch feeds, others are authoritative registries.

**Decision:** Build the Companies House collector before Product Hunt (and the other sources).

**Consequences:** Companies House is structured government data behind a free API with no rate limits, so it is cheap to query at scale. Director history enables serial-founder detection — a strong pre-seed signal — and incorporation records make it the highest-precision source for newly-forming companies. Starting here means the first end-to-end runs surface real, well-grounded candidates before noisier sources are layered on.
