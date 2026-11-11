# GitOps Platform Lab handbook

By Jason Stys.

Review desired, source and applied generations, dependency readiness and freshness against chronological evidence.

Separates healthy old workloads from actual convergence on the intended Git revision.

## Read the documentation

| Edition | Audience and contents |
| --- | --- |
| [project-guide.docx](reports/project-guide.docx) | User and developer guide: purpose, current usage, design, boundaries and source references. |

The editable Markdown remains the maintenance source. The Word files are readable editions, and the workbook is an evidence index rather than a test runner. See [publication identities and review](reports/publications.json) and the [documentation refresh record](reports/documentation-refresh-2026-11-09.md).

## Current usage and help

[README quick start](../README.md) is the entry point. Use the project-specific guides below before changing inputs, operating modes or deployment assumptions.

### Usage and operations

- [reconciliation review](reconciliation-review.md)
- [runbook](runbook.md)

### Design and contracts

- [architecture](architecture.md)
- [contracts](contracts.md)
- [research](research.md)

### Security and validation

- [testing](testing.md)

## Historical results and reproduction

The reviewed source is [`37432ccaecceb7a569b23e5280c678d81f101de9`](https://github.com/JasonStys/gitops-platform-lab/tree/37432ccaecceb7a569b23e5280c678d81f101de9). The observed functional workflow baseline is `37432ccaecceb7a569b23e5280c678d81f101de9`; those observations are recorded at `2026-11-10T05:25:40.628667+00:00`. They do not certify an unrun later revision.

- [Detailed recorded validation](reports/reconciliation-2026-11-09.md)
- [Current Actions](https://github.com/JasonStys/gitops-platform-lab/actions) records later integration checks separately.
- Preserve dated measurements and follow the existing testing guide to reproduce them; a test-source inventory alone does not establish execution.

## Practical boundaries

- Supplied observations and proof references are not authenticated collection or verified network verdicts.
- A healthy old workload does not prove convergence on the desired source revision.
- Cluster examples are isolated lab validation, not automatic production rollout or workstation enforcement.

## Maintaining these editions

Update the editable usage/design/test documents first. Rebuild and visually review every Word page and workbook tab before replacing an edition; verify the exact binary digests and evidence source in publications.json. Keep account data, logs with secrets, installed-app state and private test stores out of documentation. Source and release assets retain their existing security and licensing boundaries.

## Native offline application

[Complete usage, profile privacy and build](native-application.md) · [Dated local validation](reports/native-workbench-2026-11-11.md). Historical Office editions retain their recorded source baseline.
