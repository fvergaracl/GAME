"""Model layer - the database schema.

SQLModel/SQLAlchemy table definitions for every persisted entity. Each model
inherits :class:`app.model.base_model.BaseModel`, which contributes the common
``id``, timezone-aware ``created_at``/``updated_at``, and the
``apiKey_used``/``oauth_user_id`` audit columns to every table. See the
:doc:`domain model </domain-model>` for the entity-relationship overview.
"""
