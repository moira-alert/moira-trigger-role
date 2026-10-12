.PHONY: all install verify tests_unit lint triggers_staging triggers_production

all: install tests_unit lint triggers_staging triggers_production verify

install: # link local moira-trigger-role instead of downloading released version from Ansible Galaxy
	mkdir -p roles
	ln -sfn ../.. roles/moira-alert.moira-trigger-role

tests_unit: # unit tests (no fake api server required)
	python3 -m pytest tests/unit -v

lint: # static checks
	yamllint -c .yamllint .
	ansible-lint -c .ansible-lint

triggers_staging: # manage triggers for staging
	ansible-playbook -i staging --connection=local -vv site.yml

triggers_production: # manage triggers for production
	ansible-playbook -i production --connection=local -vv site.yml

verify: # verify creation and idempotency against the fake api
	ansible-playbook -i staging -v verify.yml