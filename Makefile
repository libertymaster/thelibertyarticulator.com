MODE ?= dev
.PHONY: prepare dev check contracts test backup
prepare:
	./ops/prepare.sh
dev:
	./ops/dev.sh --demo
check:
	MODE=$(MODE) ./ops/check_configs.sh
contracts:
	python ops/export_contracts.py
test:
	DJANGO_SETTINGS_MODULE=config.settings.testing python manage.py test tests.django_tests
	python ops/export_contracts.py --check
	cd frontend && npm run build && npm test
backup:
	MODE=prod ./ops/backup.sh
