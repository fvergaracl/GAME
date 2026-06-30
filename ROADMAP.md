# GAME Roadmap

An honest snapshot of what is stable, what is experimental, what is planned,
and what is deliberately out of scope. It exists so that anyone evaluating or
extending GAME knows what they can rely on today.

This is a living document, not a delivery commitment. Status reflects the
state of `main`; dates are intentionally absent.

## Maturity levels

- **Stable** - production-ready; breaking changes go through deprecation.
- **Experimental** - usable, but the surface or behavior may still change; not
  yet recommended for production-critical paths.
- **Planned** - intended, not yet built.
- **Not planned** - deliberately out of scope today.

## Subsystem status

| Subsystem | Status | Notes |
|---|---|---|
| Core scoring engine (built-in strategy classes) | **Stable** | `BaseStrategy` + registry; `default` is the recommended baseline. |
| Points, wallets, points-to-coins conversion | **Stable** | Append-only ledger; conversions record `appliedConversionRate`. Point assignment is atomic; the conversion path is not yet single-transaction (a known limitation, see below). |
| REST API (games, tasks, users, points, exports) | **Stable** | Versioned under `/api/v1`; OpenAPI at `/docs` and `/redocs`. |
| Authentication (API key + Keycloak OAuth2) | **Stable** | Per-key scoping and rate limiting. |
| Data exports (CSV-style history) | **Stable** | Recorded in `ExportAuditLog`. |
| No-code DSL (custom strategies) | **Experimental** | Production-usable and sandboxed; scoring semantics mirror `default`. Editor and block reference still evolving. |
| Dashboard (React admin UI) | **Experimental** | Works for core flows; known UX gaps tracked internally. |
| Redis cache | **Experimental / optional** | Off by default; enable via configuration. |
| `getis_ord_gi_star` (Gi\* spatial strategy) | **Experimental** | Hot-spot computation works standalone but is **not wired into scoring**: it does not subclass `BaseStrategy` and its `calculate_points` is a stub. |
| Refunds / reversals / ledger adjustments | **Planned** | No refund operation today; the ledger is immutable. Reserved transaction types exist in the model but are never emitted (see below). |
| Point/coin transfers between users | **Planned** | Reserved `TransferPoints` / `TransferCoins` types; not implemented. |

## Planned

- **Refunds and adjustments.** A first-class, ledger-preserving way to reverse
  or correct an award or a conversion. It is intended to add new transaction
  types rather than mutate existing rows, keeping the audit trail intact.
  Until it lands, see "Corrections and reversibility" in the integration guide
  (`docs/source/integrating.rst`).
- **Wiring the spatial strategy.** Make `getis_ord_gi_star` subclass
  `BaseStrategy` and emit points so the Gi\* hot-spot signal can drive scoring.
- **Transfers between users.** Implement the reserved transfer transaction
  types.
- **Atomic points-to-coins conversion.** Wrap the conversion balance update and
  its ledger row in a single transaction, so a crash between them can no longer
  leave a conversion without a recording row. See "Known limitations" in the
  integration guide (`docs/source/integrating.rst`).

## Not planned (today)

- Multi-currency wallets or external payment processing.
- A hosted, multi-tenant SaaS control plane (GAME is self-hosted).

## Influencing the roadmap

Open or upvote a [GitHub issue](https://github.com/fvergaracl/GAME/issues), or
start a [discussion](https://github.com/fvergaracl/GAME/discussions).
Contributions toward any **Planned** item are very welcome - start with
[CONTRIBUTING.md](CONTRIBUTING.md).
