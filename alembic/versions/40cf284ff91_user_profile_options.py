"""user profile options

Revision ID: 40cf284ff91
Revises: 121f4440c4ec
Create Date: 2013-06-22 18:28:00.026358

"""

# revision identifiers, used by Alembic.
revision = '40cf284ff91'
down_revision = '121f4440c4ec'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import func


def upgrade():
	op.add_column(
		"users",
		sa.Column("show_rooms_joined", sa.Boolean, nullable=False, server_default="1"),
	)

	op.add_column(
		"users",
		sa.Column("show_rooms_owned", sa.Boolean, nullable=False, server_default="1"),
	)

	op.add_column(
		"users",
		sa.Column("show_rooms_starred", sa.Boolean, nullable=False, server_default="1"),
	)


def downgrade():
	op.drop_column("users", "show_rooms_joined")
	op.drop_column("users", "show_rooms_owned")
	op.drop_column("users", "show_rooms_starred")
