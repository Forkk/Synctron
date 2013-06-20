"""add users_can_move option

Revision ID: 121f4440c4ec
Revises: 1644a44a4b39
Create Date: 2013-06-19 22:09:04.989775

"""

# revision identifiers, used by Alembic.
revision = '121f4440c4ec'
down_revision = '1644a44a4b39'

from alembic import op
import sqlalchemy as sa


def upgrade():
	op.add_column(
		"rooms",
		sa.Column("users_can_move", sa.Boolean, default=1, nullable=False),
	)


def downgrade():
	op.drop_column(
		"rooms",
		"users_can_move",
	)
