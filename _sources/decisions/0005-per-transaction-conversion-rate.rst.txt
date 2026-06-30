==================================================
ADR 0005: Conversion rate captured per transaction
==================================================

:Status: Accepted

Context
=======

A wallet's ``conversionRate`` (points per coin) can change over time. A past
conversion must remain explainable against the rate that was *actually*
applied, not whatever the wallet's rate happens to be now.

Decision
========

Each ``ConvertPointsToCoins`` ledger row stamps
``appliedConversionRate = wallet.conversionRate`` at conversion time
(``app/services/user_service.py``); the column lives on the ledger model
(``app/model/wallet_transactions.py``). The field is only meaningful for
conversions; ``AssignPoints`` rows on the engine scoring path leave it at
``0`` (``app/services/user_points/persistence.py``), since no conversion
happens on award.

Consequences
============

* Historical conversions stay auditable and replayable even after the wallet
  rate is changed: the rate travels with the row.
* Cost: a denormalized rate snapshot per conversion row.
* A conversion can only be traced to its rate if the ledger row was written -
  see the conversion-atomicity caveat in :ref:`known-limitations`.

See also
========

* :doc:`/domain-model` - the ``WalletTransactions`` fields.
* :doc:`/integrating` - "Wallets & the economy".
* :doc:`0002-append-only-wallet-ledger` - the ledger this rate lives in.
