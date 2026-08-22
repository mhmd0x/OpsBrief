"""add work order lifecycle timestamps

Revision ID: 4d2f8c1a7b6e
Revises: 06ceeebbb833
Create Date: 2026-08-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4d2f8c1a7b6e"
down_revision: Union[str, Sequence[str], None] = "06ceeebbb833"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "work_orders",
        sa.Column(
            "failure_reported_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "work_orders",
        sa.Column(
            "repair_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "work_orders",
        sa.Column(
            "restored_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("work_orders", "restored_at")
    op.drop_column("work_orders", "repair_started_at")
    op.drop_column("work_orders", "failure_reported_at")
