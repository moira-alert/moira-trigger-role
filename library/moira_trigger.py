#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, SKB Kontur.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

'''Ansible module to create, update and delete Moira triggers

'''

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: moira_trigger
short_description: Working with large number of triggers in Moira.
description:
    - Create new triggers.
    - Edit existing triggers parameters.
    - Delete triggers.
author: 'SKB Kontur'
requirements:
    - 'python >= 2.7'
    - 'moira-client >= 2.0'
options:
  api_url:
    description:
      - Url of Moira API.
    required: True
  auth_custom:
    description:
      - Auth custom headers.
    required: False
    default: None
  auth_user:
    description:
      - Auth User.
    required: False
    default: None
  auth_pass:
    description:
      - Auth Password.
    required: False
    default: None
  login:
    description:
      - Auth Login.
    required: False
    default: None
  state:
    description:
      - Desired state of a trigger.
      - Use state 'present' to create and edit existing triggers.
      - Use state 'absent' to delete triggers.
    required: True
    choices: ['present', 'absent']
  id:
    description:
      - Trigger id.
    required: True
  name:
    description:
      - Trigger name.
    required: True
  tags:
    description:
      - List of trigger tags.
    required: True
  targets:
    description:
      - List of trigger targets.
    required: True
  warn_value:
    description:
      - Value to set WARN status.
    required: False
    default: None
  error_value:
    description:
      - Value to set ERROR status.
    required: False
    default: None
  trigger_type:
    description:
      - Type of a trigger.
    required: False
    choices: ['rising', 'falling', 'expression']
  expression:
    description:
      - C-like expression.
    required: False
    default: ''
  ttl:
    description:
      - Time To Live.
    required: False
    default: 600
  ttl_state:
    description:
      - Trigger state at the expiration of TTL.
    required: False
    default: 'NODATA'
    choices: ['NODATA', 'ERROR', 'WARN', 'OK']
  is_remote:
    description:
      - Use remote storage.
    required: False
    default: False
  desc:
    description:
      - Trigger description.
    required: False
    default: ''
  disabled_days:
    description:
      - Days for trigger to be in silent mode.
    required: False
    default: []
  timezone_offset:
    description:
      - Timezone offset (minutes)
    required: False
    default: 0
  start_hour:
    description:
      - Start hour to send alerts.
    required: False
    default: 0
  start_minute:
    description:
      - Start minute to send alerts.
    required: False
    default: 0
  end_hour:
    description:
      - End hour to send alerts.
    required: False
    default: 23
  end_minute:
    description:
      - End minute to send alerts.
    required: False
    default: 59
notes:
    - More details at https://github.com/moira-alert/moira-trigger-role.
'''

EXAMPLES = '''
# Trigger creation example.
- name: MoiraAnsible
  moira_trigger:
     api_url: http://localhost/api/
     state: present
     id: '{{ item.id }}'
     name: '{{ item.name }}'
     desc: trigger test description
     warn_value: 300
     error_value: 600
     ttl_state: ERROR
     tags:
       - 'Project'
       - 'Service'
     targets: '{{ item.targets }}'
     disabled_days:
       ? Mon
       ? Wed
  with_items:
    - id: trigger_1
      name: Trigger 1
      targets:
        - 'prefix.target1.postfix'
    - id: trigger_2
      name: Trigger 2
      targets:
        - 'prefix.target2.postfix'
'''

RETURN = '''
result:
  description: trigger state has been changed
  returned: always
  type: dict
  sample: {'test2': 'trigger has been created'}
'''

from functools import wraps

try:
    from moira_client import Moira
    from moira_client.models.trigger import DAYS_OF_WEEK
    HAS_MOIRA_CLIENT = True
except ImportError:
    HAS_MOIRA_CLIENT = False
    MISSING_MOIRA_CLIENT = (
        'Unable to import required module. '
        'Make sure you have moira-client installed: '
        'pip install moira-client')

from ansible.module_utils.basic import AnsibleModule

fields = {
    'api_url': {
        'type': 'str',
        'required': True},
    'auth_custom': {
        'type': 'dict',
        'required': False,
        'default': None,
        'no_log': True},
    'auth_user': {
        'type': 'str',
        'required': False,
        'default': None},
    'auth_pass': {
        'type': 'str',
        'required': False,
        'default': None,
        'no_log': True},
    'login': {
        'type': 'str',
        'required': False,
        'default': None},
    'state': {
        'type': 'str',
        'required': True,
        'choices': ['present', 'absent']},
    'id': {
        'type': 'str',
        'requred': True},
    'name': {
        'type': 'str',
        'required': True},
    'tags': {
        'type': 'list',
        'required': True},
    'targets': {
        'type': 'list',
        'required': True},
    'warn_value': {
        'type': 'float',
        'required': False,
        'default': None},
    'error_value': {
        'type': 'float',
        'required': False,
        'default': None},
    'trigger_type': {
        'type': 'str',
        'choices': ['rising', 'falling', 'expression'],
        'required': False},
    'expression': {
        'type': 'str',
        'required': False,
        'default': ''},
    'ttl': {
        'type': 'int',
        'required': False,
        'default': 600},
    'ttl_state': {
        'type': 'str',
        'required': False,
        'choices': ['NODATA', 'ERROR', 'WARN', 'OK'],
        'default': 'NODATA'},
    'is_remote': {
        'type': 'bool',
        'required': False,
        'default': False},
    'desc': {
        'type': 'str',
        'required': False,
        'default': ''},
    'disabled_days': {
        'type': 'list',
        'required': False,
        'default': []},
    'timezone_offset': {
        'type': 'int',
        'required': False,
        'default': 0},
    'start_hour': {
        'type': 'int',
        'required': False,
        'default': 0},
    'start_minute': {
        'type': 'int',
        'required': False,
        'default': 0},
    'end_hour': {
        'type': 'int',
        'required': False,
        'default': 23},
    'end_minute': {
        'type': 'int',
        'required': False,
        'default': 59}}

module = AnsibleModule(
    argument_spec=fields,
    supports_check_mode=True)

if not HAS_MOIRA_CLIENT:
    module.fail_json(msg=MISSING_MOIRA_CLIENT)

moira_api = Moira(
    api_url=module.params['api_url'],
    auth_custom=module.params['auth_custom'],
    auth_user=module.params['auth_user'],
    auth_pass=module.params['auth_pass'],
    login=module.params['login'])

preimage = {
    'id': module.params['id'],
    'name': module.params['name'],
    'targets': module.params['targets'],
    'warn_value': module.params['warn_value'],
    'error_value': module.params['error_value'],
    'ttl': module.params['ttl'],
    'ttl_state': module.params['ttl_state'],
    'expression': module.params['expression'],
    'is_remote': module.params['is_remote'],
    'trigger_type': module.params['trigger_type'],
    'desc': module.params['desc'],
    'tags': module.params['tags'],
    'disabled_days': set(module.params['disabled_days']),
    'sched': {
        'days': [{
            'name': day,
            'enabled': day not in module.params['disabled_days']} for day in DAYS_OF_WEEK],
        'startOffset': (60 * module.params['start_hour']) + module.params['start_minute'],
        'endOffset': (60 * module.params['end_hour']) + module.params['end_minute'],
        'tzOffset': module.params['timezone_offset']}}

def handle_exception(function):

    '''Handling occurred exceptions.

    Returns:
        Default function JSON result on success,
        JSON with diagnostic info otherwise.

    '''

    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as occurred:
            return {
                'failed': {
                    'method': function.__name__,
                    'error': occurred.__class__.__name__,
                    'details': str(occurred)}}

    return wrapper


class MoiraTrigger(object):

    '''Moira trigger.

    Args:
        trigger preimage (dict): trigger preimage.

    Attributes:
        preimage (dict): trigger preimage.
        image (dict): trigger image if exists.

    '''

    def __init__(self, trigger_preimage):

        self._id = trigger_preimage['id']
        self.preimage = trigger_preimage

    def has_image(self):

        '''Check if image exists.

        Returns:
            True if found, False otherwise.

        '''

        self.image = moira_api.trigger.fetch_by_id(
            self._id)

        if self.image is not None:
            return True

        return False

    def merge_with(self, image):

        '''Merge preimage with given image.

        Args:
            image (dict): trigger image.

        Returns:
            True if merged, False otherwise.

        '''

        score = 0

        self.preimage['tags'].sort()
        image.__dict__['tags'].sort()

        for field in 'name', 'desc':
            self.preimage[field] = preimage[field].decode("utf-8")

        for field in self.preimage:
            if not field == 'id' and \
               not image.__dict__[field] == self.preimage[field]:
                image.__dict__[field] = self.preimage[field]
                if not field == 'trigger_type':
                    score += 1

        if score != 0:
            return True

        return False


class MoiraTriggerManager(object):

    '''Create, edit and delete Moira triggers.

    Args:
        dry_run (bool): enables check mode.

    '''

    def __init__(self, dry_run):

        self.dry_run = dry_run
        self.has_diff = False

    @handle_exception
    def remove(self, moira_trigger):

        '''Remove trigger if exists.

        Args:
            moira_trigger (object): moira trigger.

        Returns:
            JSON with trigger id and trigger state on success,
            JSON with diagnostic info if failed.

        '''

        if not moira_trigger.has_image():
            return {moira_trigger._id: 'no id found for trigger'}

        if not self.dry_run and \
           moira_api.trigger.delete(moira_trigger._id):
            self.has_diff = True

        return {moira_trigger._id: 'trigger has been removed'}

    @handle_exception
    def edit(self, moira_trigger):

        '''Edit existing trigger.

        Args:
            moira_trigger (object): moira trigger.

        Returns:
            JSON with trigger id and trigger state on success,
            JSON with diagnostic info if failed.

        '''

        if not moira_trigger.has_image():

            trigger = moira_api.trigger.create(
                **moira_trigger.preimage)

            result = 'trigger has been created'

            if not self.dry_run:
                self.has_diff = True
                trigger.save()

        else:

            trigger = moira_trigger.image
            result = 'trigger has been updated'

        if not self.dry_run and \
           moira_trigger.merge_with(trigger):
            self.has_diff = True
            trigger.update()

        return {moira_trigger._id: result}

    @handle_exception
    def define_state(self, state, moira_trigger):

        '''Define trigger state.

        Args:
            state (str): desired trigger state.
            moira_trigger (object): moira trigger.

        Returns:
            JSON with trigger id and trigger state on success,
            JSON with diagnostic info if failed.

        '''

        if state == 'present':
            return self.edit(moira_trigger)

        elif state == 'absent':
            return self.remove(moira_trigger)


def main():

    '''Interact with Moira API via Ansible.

    '''

    manager = MoiraTriggerManager(dry_run=module.check_mode)
    trigger = MoiraTrigger(trigger_preimage=preimage)

    result = manager.define_state(
        state=module.params['state'], moira_trigger=trigger)

    if 'failed' in result:
        module.fail_json(msg='Unable to define trigger state', meta=result)

    else:
        module.exit_json(changed=manager.has_diff, result=result)


if __name__ == '__main__':
    main()
