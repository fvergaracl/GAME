=====================================
ADR 0004: Idempotency keys for awards
=====================================

:Status: Accepted

Context
=======

Clients retry award requests on network failure. A naive retry would award the
same event twice.

Decision
========

Before inserting, the persistence layer derives an idempotency key from the
first non-empty of ``eventId``, ``idempotencyKey`` or ``correlationId``
(``app/services/user_points/persistence.py``) and short-circuits if a matching
row already exists. The guarantee is enforced at the database by
``UniqueConstraint("userId", "taskId", "idempotencyKey")``
(``app/model/user_points.py``, constraint
``uq_user_points_user_task_idempotency``), so a duplicate can never be
persisted even if the read check races.

Consequences
============

* Awards are safe to retry: a repeated request with the same key returns the
  existing assignment instead of creating a second one.
* The dedupe scope is ``(user, task, key)`` - the same key under a different
  task is a different award. A ``null`` key is allowed (the un-deduped path).
* Under a true concurrent retry race, the loser of the unique-constraint race
  receives ``409 Conflict`` rather than the original success body. The
  no-double-award guarantee still holds. See :ref:`known-limitations`.

See also
========

* :doc:`/domain-model` - "Idempotency & concurrency".
* :doc:`/integrating` - the idempotency-key request header.
* :doc:`0003-atomic-points-write` - the transaction this builds on.
