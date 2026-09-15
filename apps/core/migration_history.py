"""Pure comparison for a read-only migration-history guard."""


def unknown_migrations(applied, available, replacements):
    known = set(available)
    # Django may retain records of migrations covered by a squashed migration.
    for replaced in replacements.values():
        known.update(replaced)
    return sorted(set(applied) - known)
