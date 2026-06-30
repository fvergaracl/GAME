==================================
ADR 0003: Atomic points write
==================================

:Status: Accepted

Context
=======

Awarding points touches three rows: the ``UserPoints`` record, the wallet
balance, and the ledger entry. A partial failure could leave a points row with
no wallet effect, or a balance change with no points row.

Decision
========

``_persist_points_wallet_and_transaction``
(``app/services/user_points/persistence.py``) opens **one** session and does
all three writes with ``auto_commit=False``, committing once at the end and
rolling back on any exception. The repository ``create(..., auto_commit=False)``
contract is what lets a service compose several writes into a single
transaction; transaction boundaries live in the service layer, not the
repository.

Consequences
============

* The point-assignment write is all-or-nothing: no torn state.
* The service layer is the only place that should compose multi-row writes.
* This atomicity covers **assignment only**. The points-to-coins conversion
  path is *not* yet wrapped in a single transaction - see :ref:`known-limitations`.

See also
========

* :doc:`/architecture` - "the life of a scoring request" and the
  ``auto_commit=False`` compose-one-transaction contract.
* :doc:`0004-idempotency-keys` - the retry-safety guarantee built on top.
