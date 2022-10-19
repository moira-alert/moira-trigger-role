.PHONY: all triggers_staging triggers_production

all: install triggers_staging triggers_production

install: # install moira-trigger-role
	ansible-galaxy install moira-alert.moira-trigger-role --roles-path=roles --force

triggers_staging: # manage triggers for staging
	ansible-playbook -i staging --connection=local -vv site.yml

triggers_production: # manage triggers for production
	ansible-playbook -i production --connection=local -vv site.yml
