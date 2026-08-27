# Baseline fixtures

`initial_categories.json` and `initial_keywords.json` contain non-secret editorial taxonomy only. Load them after migrations with:

```bash
python manage.py loaddata fixtures/initial_categories.json fixtures/initial_keywords.json
```

The records use stable primary keys so child categories can be added in later fixtures. Treat changes to names and slugs as editorial migrations once URLs have been published.

`initial_users.json` is deliberately empty. Never distribute a default password or production account in a fixture. Provision the first recovery superuser interactively with `createsuperuser`, then use FusionAuth for managed identities.
