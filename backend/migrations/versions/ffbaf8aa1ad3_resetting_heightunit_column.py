"""Resetting heightunit column

Revision ID: ffbaf8aa1ad3
Revises: b080b6e620e0
Create Date: 2025-08-28 00:40:38.311179

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa 


# revision identifiers, used by Alembic.
revision: str = 'ffbaf8aa1ad3'
down_revision: Union[str, None] = 'b080b6e620e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('user_accounts', 'height_unit')
    op.execute("DROP TYPE IF EXISTS heightunit")

    heightunit_enum = sa.Enum('CENTIMETERS', 'INCHES', name='heightunit')
    heightunit_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('user_accounts', sa.Column('height_unit', heightunit_enum, nullable=True))
    
def downgrade() -> None:
    """Downgrade schema."""
    pass
