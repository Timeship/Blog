"""fifth migratation

Revision ID: 2f6572e0534
Revises: 57962b6e1e5
Create Date: 2015-11-06 09:55:44.148604

"""

# revision identifiers, used by Alembic.
revision = '2f6572e0534'
down_revision = '57962b6e1e5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('posts', sa.Column('body_html', sa.Text(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('posts', 'body_html')
    ### end Alembic commands ###
