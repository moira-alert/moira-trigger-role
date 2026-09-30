.PHONY: all triggers_staging triggers_production

all: install triggers_staging triggers_production

install: # link local moira-trigger-role instead of downloading released version from Ansible Galaxy
	mkdir -p roles
	ln -sfn ../.. roles/moira-alert.moira-trigger-role

triggers_staging: # manage triggers for staging
	ansible-playbook -i staging --connection=local -vv site.yml

triggers_production: # manage triggers for production
	ansible-playbook -i production --connection=local -vv site.yml
