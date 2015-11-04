"""third migration

Revision ID: 45161288044
Revises: 4eae9637f8f
Create Date: 2015-11-04 16:06:15.627327

"""

# revision identifiers, used by Alembic.
revision = '45161288044'
down_revision = '4eae9637f8f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('avatar_hash', sa.String(length=32), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'avatar_hash')
    ### end Alembic commands ###
