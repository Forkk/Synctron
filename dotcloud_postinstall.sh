#!/bin/sh
# Post-install database migrations.

. $HOME/venv/bin/activate

alembic upgrade head
