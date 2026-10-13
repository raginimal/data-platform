# ai-data-platform Architecture

## Purpose

`ai-data-platform` is a local-first data platform for ingesting approved sample data, transforming it with dbt, validating governed datasets, and producing lineage evidence for future AI-assisted explanations.

The project uses Python for orchestration and boundary validation, DuckDB for local persistence, and dbt for SQL transformations. BigQuery is a future provider overlay, not part of the initial runtime.

The reusable foundation remains authoritative for policy, workflow, CI/CD, agent review, and human approval. Project decisions are recorded here and in the architecture baseline.

## Requirements and boundaries

The platform will support:

- Synthetic or explicitly approved local-file ingestion.
- Raw and curated datasets in DuckDB.
- dbt sources, staging models, intermediate models, and curated marts.
- Versioned contracts for shared, persisted, and AI-consumed datasets.
- Deterministic schema, quality, compatibility, and freshness checks.
- Lineage and upstream/downstream impact analysis from dbt artifacts.
- A future bounded assistant that explains approved contracts, quality results, and lineage.

The initial project will not provide production ingestion, streaming, multi-tenant access, cloud provisioning, autonomous AI actions, unrestricted raw-data querying, or a separate catalog/lineage service.

## Application pattern

Use a modular monolith with library and command-line interfaces. Dependencies point inward:

1. Interfaces expose commands and future service adapters.
2. Application orchestration coordinates ingestion, transformation, validation, lineage, and explanation workflows.
3. Domain modules own contracts, quality, lineage, and explanation rules.
4. Infrastructure adapters isolate DuckDB, the filesystem, dbt, and future model providers.
5. Configuration and governance assets remain outside domain logic.

Python owns orchestration and boundary validation. SQL and dbt own transformation semantics. Domain modules must not depend directly on BigQuery or a model vendor.

## Components

| Component | Responsibility | Dependencies |
|---|---|---|
| Ingestion | Validate approved inputs, classify data, create run metadata, load raw tables | Filesystem adapter, contracts, DuckDB adapter |
| DuckDB adapter | Manage local connections, transactions, typed tables, and queries | DuckDB |
| dbt project | Define sources, transformations, marts, tests, documentation, and artifacts | DuckDB profile initially |
| Contract and quality | Validate schemas, compatibility, completeness, uniqueness, ranges, accepted values, and freshness | Contract metadata, DuckDB, dbt artifacts |
| Lineage | Parse dbt artifacts and calculate upstream/downstream impact | dbt manifest and catalog |
| Explanation | Explain governed metadata and evidence with limitations and refusal boundaries | Contracts, quality, lineage, future model adapter |

No component may introduce hidden network calls or bypass the contract boundary.

## Repository structure

Project-owned implementation will use the existing foundation boundaries:

```text
src/ai_data_platform/
	application/       orchestration
	domain/            contracts, quality, lineage, explanations
	adapters/          DuckDB, filesystem, dbt, future model providers
	cli/               command-line interface
data/
	seeds/             synthetic inputs
	dbt/               dbt project, models, tests, macros, profiles
tests/
	unit/              deterministic Python logic
	integration/       DuckDB and dbt workflows
	e2e/               complete governed workflows
ai/                  model, prompt, guardrail, and evaluation assets
docs/adr/            architecture decisions and boundary changes
```

Generated dbt artifacts and local DuckDB files are not source-controlled. Existing `agents/`, `skills/`, `policies/`, `scripts/`, `config/`, and `infrastructure/` directories are reused rather than duplicated.

## Testing and security

- Unit tests are required for parsing, contracts, quality rules, lineage impact, and explanation boundaries.
- Integration tests must cover file-to-DuckDB ingestion and dbt execution.
- End-to-end tests must cover ingestion through curated output and governed explanation.
- Fixtures must be synthetic or de-identified; production or restricted data is prohibited without approval.
- Inputs are untrusted and must be validated at every boundary.
- Secrets and credentials never enter source control, prompts, fixtures, logs, or model outputs.
- Dependencies are declared, justified, pinned or constrained, and scanned.
- Future identities use least privilege and environment separation.
- A real model provider requires model registration, data-boundary review, guardrails, evaluations, cost controls, and human escalation.

## Automatic enforcement

The project preserves and extends the foundation checks:

- `bash scripts/check.sh` remains the local pre-commit gate.
- `scripts/validate-baseline.sh` classifies boundary impact from changed paths.
- `scripts/validate.sh` and `scripts/validate-policies.sh` remain authoritative repository and policy checks.
- CI continues to run the policy workflow and baseline guard on pull requests.
- Stack-specific lint, test, dependency, contract, dbt, and secret checks may be added as overlays without weakening foundation checks.

The baseline guard must classify changes to project architecture, data stores and contracts, AI integration, model providers, deployment, environments, and CI/CD. `ARCHITECTURE_CHANGE` requires an ADR with `Baseline impact: change` after the baseline is approved; agents advise and humans approve.

## Architecture rules

- Shared or AI-consumed datasets require versioned contracts with owner, consumers, classification, schema, quality, retention, and access metadata (`DATA-CON-001` through `DATA-CON-004`).
- DuckDB-specific behavior stays behind the adapter boundary.
- Transformation logic stays in dbt SQL; orchestration stays in Python.
- BigQuery-specific behavior stays in a future provider overlay.
- Lineage comes from dbt artifacts until a separately approved platform is introduced.
- AI explanations consume governed evidence, not unrestricted raw data.
- New stores, providers, services, public interfaces, trust boundaries, or breaking changes require an ADR under `docs/adr/`.
- Secrets, hidden network calls, undocumented data copies, and vendor-specific logic in policy paths are prohibited.

## Source of truth and approval

The detailed architecture policies are under `policies/architecture/`. The locked project boundaries are defined in `docs/architecture/baseline.yaml`. The baseline remains `draft` until the architecture owner records approval, approver, date, and approving ADR. Changes are classified by `bash scripts/validate-baseline.sh` and follow the approval matrix in `docs/governance/approval-matrix.md`.
