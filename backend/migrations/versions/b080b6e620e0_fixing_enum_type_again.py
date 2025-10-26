"""Fixing enum type again

Revision ID: b080b6e620e0
Revises: 05d11468ba82
Create Date: 2025-08-27 17:12:52.330068

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa 


# revision identifiers, used by Alembic.
revision: str = 'b080b6e620e0'
down_revision: Union[str, None] = '05d11468ba82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the column first
    op.drop_column('user_accounts', 'height_unit')
    
    # Drop the old enum type
    op.execute("DROP TYPE IF EXISTS heightunit")
    
    # Create new enum with correct values
    heightunit_enum = sa.Enum('cm', 'in', name='heightunit')
    heightunit_enum.create(op.get_bind(), checkfirst=True)
    
    # Add the column back with correct enum
    op.add_column('user_accounts', sa.Column('height_unit', heightunit_enum, nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the column
    op.drop_column('user_accounts', 'height_unit')
    
    # Drop the current enum type
    op.execute("DROP TYPE IF EXISTS heightunit")
    
    # Create old enum with wrong values (for downgrade compatibility)
    heightunit_enum = sa.Enum('CENTIMETERS', 'INCHES', name='heightunit')
    heightunit_enum.create(op.get_bind(), checkfirst=True)
    
    # Add the column back with old enum
    op.add_column('user_accounts', sa.Column('height_unit', heightunit_enum, nullable=True))
