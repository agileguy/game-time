# Database Migrations

This directory contains Alembic database migrations for the Game Time application.

## Creating Migrations

### Auto-generate migration from model changes
```bash
alembic revision --autogenerate -m "Add user table"
```

### Create empty migration
```bash
alembic revision -m "Custom migration"
```

## Running Migrations

### Upgrade to latest
```bash
alembic upgrade head
```

### Upgrade one version
```bash
alembic upgrade +1
```

### Downgrade one version
```bash
alembic downgrade -1
```

### Downgrade to specific revision
```bash
alembic downgrade <revision_id>
```

## Checking Migration Status

### Show current revision
```bash
alembic current
```

### Show migration history
```bash
alembic history
```

### Show pending migrations
```bash
alembic show
```

## Best Practices

1. **Always review auto-generated migrations** - Alembic's autogenerate is smart but not perfect
2. **Test migrations in both directions** - Ensure upgrade and downgrade work
3. **Use meaningful migration messages** - Future you will thank you
4. **Keep migrations small and focused** - One logical change per migration
5. **Never edit applied migrations** - Create a new migration instead
6. **Version control all migrations** - They are code!

## Migration Naming Convention

Migrations are automatically named with timestamp and slug:
```
20240115_1430-abc123_add_user_table.py
```

## Common Operations

### Adding a column
```python
def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(255), nullable=False))

def downgrade() -> None:
    op.drop_column('users', 'email')
```

### Creating an index
```python
def upgrade() -> None:
    op.create_index('ix_users_email', 'users', ['email'])

def downgrade() -> None:
    op.drop_index('ix_users_email', table_name='users')
```

### Adding a foreign key
```python
def upgrade() -> None:
    op.create_foreign_key(
        'fk_posts_user_id',
        'posts', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )

def downgrade() -> None:
    op.drop_constraint('fk_posts_user_id', 'posts', type_='foreignkey')
```
