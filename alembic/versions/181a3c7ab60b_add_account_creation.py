"""add account creation and activity columns

Revision ID: 181a3c7ab60b
Revises: 40cf284ff91
Create Date: 2013-06-23 13:21:26.649872

"""

# revision identifiers, used by Alembic.
revision = '181a3c7ab60b'
down_revision = '40cf284ff91'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.sql import table, column
from datetime import datetime


def upgrade():
	op.add_column(
		"users",
		sa.Column("account_created", sa.DateTime, nullable=False),
	)

	op.add_column(
		"users",
		sa.Column("last_activity", sa.DateTime, nullable=True),
	)

	# Set the account creation dates for all users to the current date and time.
	users = table("users", column("account_created", sa.DateTime))
	op.execute(users.update().values({ "account_created": datetime.now() }))


def downgrade():
	op.drop_column("users", "account_created")
	op.drop_column("users", "last_activity")
