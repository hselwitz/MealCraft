"""Track which selected meals a grocery list covers."""
from alembic import op
import sqlalchemy as sa
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("grocery_lists", sa.Column("scope", sa.JSON(), nullable=True))

def downgrade():
    op.drop_column("grocery_lists", "scope")
