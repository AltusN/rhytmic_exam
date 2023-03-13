"""empty message

Revision ID: 0b40cefba662
Revises: 10b383b52587
Create Date: 2020-02-16 18:01:25.202874

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0b40cefba662'
down_revision = '10b383b52587'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('exam_questions', sa.Column('exam_level', sa.String(length=20), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('exam_questions', 'exam_level')
    # ### end Alembic commands ###
