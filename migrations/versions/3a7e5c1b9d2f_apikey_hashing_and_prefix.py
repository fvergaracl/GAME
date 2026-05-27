"""apikey hashing and public prefix

Revision ID: 3a7e5c1b9d2f
Revises: 92c5b0f4a3a7
Create Date: 2026-05-25 00:00:00.000000

Repurpose ``apikey.apiKey`` to store the *public prefix* (e.g.
``gme_live_abc12345``) and add a new ``apiKeyHash`` column carrying the
sha256 hex digest of the plaintext secret. Existing rows are migrated
in-place: each legacy plaintext value is hashed, a deterministic prefix
is derived from it, and all ``apiKey_used`` foreign-key columns across
the schema are rewritten to the new prefix.
"""

import hashlib

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3a7e5c1b9d2f"
down_revision = "92c5b0f4a3a7"
branch_labels = None
depends_on = None


FK_TABLES = (
    "games",
    "gamesparams",
    "logs",
    "oauthusers",
    "tasks",
    "tasksparams",
    "useractions",
    "userpoints",
    "users",
    "wallet",
    "wallettransactions",
)


def _legacy_prefix(plaintext: str, key_hash: str) -> str:
    if "." in plaintext:
        return plaintext.split(".", 1)[0]
    return f"gme_legacy_{key_hash[:12]}"


def upgrade():
    bind = op.get_bind()

    op.add_column(
        "apikey", sa.Column("apiKeyHash", sa.String(), nullable=True)
    )

    rows = bind.execute(
        sa.text('SELECT id, "apiKey" FROM apikey')
    ).fetchall()

    if rows:
        # Drop every FK that actually references apikey.apiKey, regardless of
        # name. Earlier migrations created some FKs with op.create_foreign_key(None, ...),
        # so Postgres-assigned names don't always match the canonical pattern.
        fk_rows = bind.execute(
            sa.text(
                """
                SELECT tc.table_name, tc.constraint_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.constraint_column_usage AS ccu
                  ON tc.constraint_name = ccu.constraint_name
                 AND tc.table_schema    = ccu.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND ccu.table_name     = 'apikey'
                  AND ccu.column_name    = 'apiKey'
                """
            )
        ).fetchall()

        for table_name, constraint_name in fk_rows:
            op.execute(
                f'ALTER TABLE "{table_name}" '
                f'DROP CONSTRAINT IF EXISTS "{constraint_name}"'
            )

        discovered_fk_tables = {row[0] for row in fk_rows}
        update_tables = sorted(set(FK_TABLES) | discovered_fk_tables)

        for row in rows:
            row_id = row[0]
            legacy_plaintext = row[1]
            if legacy_plaintext is None:
                continue
            key_hash = hashlib.sha256(
                legacy_plaintext.encode("utf-8")
            ).hexdigest()
            new_prefix = _legacy_prefix(legacy_plaintext, key_hash)

            for table in update_tables:
                bind.execute(
                    sa.text(
                        f'UPDATE "{table}" '
                        f'SET "apiKey_used" = :new_prefix '
                        f'WHERE "apiKey_used" = :legacy'
                    ),
                    {
                        "new_prefix": new_prefix,
                        "legacy": legacy_plaintext,
                    },
                )

            bind.execute(
                sa.text(
                    'UPDATE apikey '
                    'SET "apiKey" = :new_prefix, '
                    '    "apiKeyHash" = :new_hash '
                    'WHERE id = :id'
                ),
                {
                    "new_prefix": new_prefix,
                    "new_hash": key_hash,
                    "id": row_id,
                },
            )

        for table in FK_TABLES:
            op.create_foreign_key(
                f"{table}_apiKey_used_fkey",
                table,
                "apikey",
                ["apiKey_used"],
                ["apiKey"],
            )

    op.alter_column("apikey", "apiKeyHash", nullable=False)
    op.create_unique_constraint(
        "uq_apikey_apiKeyHash", "apikey", ["apiKeyHash"]
    )
    op.create_index(
        "ix_apikey_apiKeyHash",
        "apikey",
        ["apiKeyHash"],
        unique=False,
    )
    op.create_index(
        "ix_apikey_apiKey_prefix",
        "apikey",
        ["apiKey"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_apikey_apiKey_prefix", table_name="apikey")
    op.drop_index("ix_apikey_apiKeyHash", table_name="apikey")
    op.drop_constraint(
        "uq_apikey_apiKeyHash", "apikey", type_="unique"
    )
    op.drop_column("apikey", "apiKeyHash")
