================================================
ADR 0002: Append-only, immutable wallet ledger
================================================

:Status: Accepted

Context
=======

Wallet balances need an auditable history. Mutating or deleting past movements
would destroy the trail that lets an operator answer "how did this balance get
here?".

Decision
========

``WalletTransactions`` rows (``app/model/wallet_transactions.py``) are only
ever inserted, never updated or deleted. Only two ``transactionType`` values
are written today: ``AssignPoints`` and ``ConvertPointsToCoins``. The model
docstring lists further reserved types (refunds, adjustments, transfers) but
states plainly that nothing in ``app/`` emits them yet, so they are a roadmap,
not behavior to rely on. There is no refund or reversal operation in the code.

Consequences
============

* A complete, replayable audit trail; balances are derived from the ledger.
* Corrections must be a new compensating entry, not an edit - and that
  compensating machinery (refunds/adjustments) is **not implemented yet**, so
  today there is no first-class way to reverse a movement.
* The "append-only" guarantee is about rows never being mutated. It does not by
  itself guarantee every movement has a row - see the conversion caveat in
  :ref:`known-limitations`.

See also
========

* :doc:`/domain-model` - the ``WalletTransactions`` entity.
* :doc:`/integrating` - "Corrections and reversibility".
* `ROADMAP.md <https://github.com/fvergaracl/GAME/blob/main/ROADMAP.md>`_ -
  refunds/adjustments are a planned item.
