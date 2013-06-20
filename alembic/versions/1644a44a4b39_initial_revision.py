"""initial revision

Revision ID: 1644a44a4b39
Revises: None
Create Date: 2013-06-19 18:50:10.542984

"""

# revision identifiers, used by Alembic.
revision = '1644a44a4b39'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
	# Create the users table.
	op.create_table(
		"users",
		sa.Column("id", sa.Integer, primary_key=True),
		sa.Column("name", sa.String(80), unique=True, nullable=False),
		sa.Column("password", sa.String(160)),
		sa.Column("email", sa.String(320)),
	)

	# Create rooms table.
	op.create_table(
		"rooms",
		sa.Column("id", sa.Integer, primary_key=True),
		sa.Column("title", sa.String(40)),
		sa.Column("slug", sa.String(40), unique=True),
		sa.Column("topic", sa.String(500)),
		sa.Column("owner_id", sa.Integer, sa.ForeignKey("users.id")),
		sa.Column("is_playing", sa.Boolean, default=False, nullable=False),
		sa.Column("start_timestamp", sa.Integer, default=0, nullable=False),
		sa.Column("last_position", sa.Integer, default=0, nullable=False),
		sa.Column("playlist_position", sa.Integer, default=0, nullable=True),
		sa.Column("is_private", sa.Boolean, default=0, nullable=False),
		sa.Column("users_can_pause", sa.Boolean, default=1, nullable=False),
		sa.Column("users_can_skip", sa.Boolean, default=1, nullable=False),
		sa.Column("users_can_add", sa.Boolean, default=1, nullable=False),
		sa.Column("users_can_remove", sa.Boolean, default=1, nullable=False),
	)

	# Create the playlist entries table.
	op.create_table(
		"playlist_entries",
		sa.Column("id", sa.Integer, primary_key=True),
		sa.Column("video_id", sa.String(15), nullable=False),
		sa.Column("position", sa.Integer, nullable=False),
		sa.Column("added_by", sa.String(80), nullable=True),
		sa.Column("room_id", sa.Integer, sa.ForeignKey("rooms.id"))
	)


	# Create the admins table.
	op.create_table(
		"admins",
		sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
		sa.Column("room_id", sa.Integer, sa.ForeignKey("rooms.id")),
	)

	# Create the stars table.
	op.create_table(
		"stars",
		sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
		sa.Column("room_id", sa.Integer, sa.ForeignKey("rooms.id")),
	)



def downgrade():
	op.drop_table("rooms")
	op.drop_table("users")
	op.drop_table("admins")
	op.drop_table("stars")
