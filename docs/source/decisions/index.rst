================
Decision records
================

.. admonition:: Who is this page for?
   :class: note

   Contributors and reviewers who want to know *why* GAME is built the way it
   is. Each record captures one architectural decision - the context that
   forced it, what was chosen, and what that costs - so a decision has a single
   home instead of being rediscovered from the code.

These are lightweight `architecture decision records
<https://adr.github.io/>`_ (MADR-style): short and numbered. A record is not a
promise that a decision is permanent; it is an honest note of what was decided
and why, at the time. Where a decision also has a richer prose home elsewhere
in this manual, the record links to it rather than duplicating it.

All records below are **Accepted** and describe the current behavior on
``main``. If a decision is later superseded, its own page records that.

.. toctree::
   :maxdepth: 1

   0001-internal-vs-external-ids
   0002-append-only-wallet-ledger
   0003-atomic-points-write
   0004-idempotency-keys
   0005-per-transaction-conversion-rate
   0006-stable-strategy-ids
   0007-dsl-sandbox
   0008-draft-on-publish-versioning
   0009-fail-fast-env-validation
   0010-cors-wraps-error-catcher
   0011-di-container-singleton-factory
   0012-sqlite-tests-postgres-prod
   0013-strategy-entrypoint-plugins
