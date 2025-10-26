"""Fixing user height column enum type

Revision ID: 05d11468ba82
Revises: bf30e4059ac6
Create Date: 2025-08-27 17:06:07.188932

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa 


# revision identifiers, used by Alembic.
revision: str = '05d11468ba82'
down_revision: Union[str, None] = 'bf30e4059ac6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('user_accounts', 'height_unit')

    heightunit_enum = sa.Enum('cm', 'in', name='heightunit')
    heightunit_enum.create(op.get_bind(), checkfirst=True)
    
    op.add_column('user_accounts', sa.Column('height_unit', heightunit_enum, nullable=True))

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user_accounts', 'height_unit')
    
    heightunit_enum = sa.Enum('CENTIMETERS', 'INCHES', name='heightunit')
    heightunit_enum.create(op.get_bind(), checkfirst=True)
    
    op.add_column('user_accounts', sa.Column('height_unit', heightunit_enum, nullable=True))
