#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2023, SKB Kontur.
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

import json
import traceback
from functools import wraps

from ansible.module_utils.basic import AnsibleModule

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
author:
    - 'SKB Kontur'
requirements:
    - 'python >= 3.6'
    - 'moira-python-client >= 5.2.1'
version_added: '1.0.0'
options:
  api_url:
    description:
      - Url of Moira API.
    type: str
    required: True
  auth_custom:
    description:
      - Auth custom headers.
    type: dict
    required: False
    default: None
  auth_user:
    description:
      - Auth User.
    type: str
    required: False
    default: None
  auth_pass:
    description:
      - Auth Password.
    type: str
    required: False
    default: None
  login:
    description:
      - Auth Login.
    type: str
    required: False
    default: None
  state:
    description:
      - Desired state of a trigger.
      - Use state 'present' to create and edit existing triggers.
      - Use state 'absent' to delete triggers.
    type: str
    required: True
    choices: ['present', 'absent']
  id:
    description:
      - Trigger id.
    type: str
    required: True
  team_id:
    description:
      - Team id of a team that owns this trigger.
    type: str
    required: False
    default: None
  name:
    description:
      - Trigger name.
    type: str
    required: True
  tags:
    description:
      - List of trigger tags.
    type: list
    elements: str
    required: True
  targets:
    description:
      - List of trigger targets.
    type: list
    elements: str
    required: True
  warn_value:
    description:
      - Value to set WARN status.
    type: float
    required: False
    default: None
  warn_for:
    description:
      - Warning value; the condition must continuously evaluate to WARN status for this many seconds before the alert fires.
    type: int
    required: False
    default: None
  warn_keep_firing_for:
    description:
      - Warning value; the alert stays active WARN many seconds after the condition no longer evaluates to this status.
    type: int
    required: False
    default: None
  error_value:
    description:
      - Value to set ERROR status.
    type: float
    required: False
    default: None
  error_for:
    description:
      - Error value; the condition must continuously evaluate to ERROR status for this many seconds before the alert fires.
    type: int
    required: False
    default: None
  error_keep_firing_for:
    description:
      - Error value; the alert stays active ERR many seconds after the condition no longer evaluates to this status.
    type: int
    required: False
    default: None
  trigger_type:
    description:
      - Type of a trigger.
    type: str
    required: False
    choices: ['rising', 'falling', 'expression']
  expression:
    description:
      - C-like expression.
    type: str
    required: False
    default: ''
  ttl:
    description:
      - Time To Live.
    type: int
    required: False
    default: 600
  ttl_state:
    description:
      - Trigger state at the expiration of TTL.
    type: str
    required: False
    default: 'NODATA'
    choices: ['NODATA', 'DEL', 'ERROR', 'WARN', 'OK']
  is_remote:
    description:
      - Use remote storage. Deprecated: use 'trigger_source' instead
    type: bool
    required: False
    default: False
  trigger_source:
    description:
      - Specify trigger source, overrides is_remote
    type: str
    required: False
    choices: ['graphite_local', 'graphite_remote', 'prometheus_remote']
  cluster_id:
    description:
      - Specify cluster id. List of available clusters can be seen in api at `https://your-moira-url/api/config`
    type: str
    required: False
  desc:
    description:
      - Trigger description.
    type: str
    required: False
    default: ''
  mute_new_metrics:
    description:
      - Mute new metrics.
    type: bool
    required: False
    default: False
  disabled_days:
    description:
      - Days for trigger to be in silent mode.
    type: list
    elements: str
    required: False
    default: []
  timezone_offset:
    description:
      - Timezone offset (minutes)
    type: int
    required: False
    default: 0
  start_hour:
    description:
      - Start hour to send alerts.
    type: int
    required: False
    default: 0
  start_minute:
    description:
      - Start minute to send alerts.
    type: int
    required: False
    default: 0
  end_hour:
    description:
      - End hour to send alerts.
    type: int
    required: False
    default: 23
  end_minute:
    description:
      - End minute to send alerts.
    type: int
    required: False
    default: 59
  alone_metrics:
    description:
      - Targets with alone metrics.
    type: dict
    required: False
    default: None
  defined_fields:
    description:
      - Names of the trigger fields explicitly provided by the caller.
      - When set, only these fields are applied and all other trigger
        attributes are left untouched. Used by the role to implement a
        partial merge.
    type: list
    elements: str
    required: False
    default: []
    version_added: '1.0.0'
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
       - Mon
       - Wed
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


try:
    from moira_client import Moira, HTTPError
    from moira_client.client import (MoiraApiError, InvalidJSONError,
                                     ResponseStructureError)

    HAS_MOIRA_CLIENT = True
except ImportError:
    HAS_MOIRA_CLIENT = False
    MISSING_MOIRA_CLIENT = (
        'Unable to import required module. '
        'Make sure you have moira-python-client installed: '
        'pip install moira-python-client')

    class _UndefinedClientError(Exception):
        pass

    HTTPError = MoiraApiError = InvalidJSONError = ResponseStructureError = \
        _UndefinedClientError

DAYS_OF_WEEK = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
MINUTES_IN_HOUR = 60

# Fields that are applied only when they are explicitly provided by the caller
# (used to implement partial merge: omitted fields are left untouched).
OPTIONAL_FIELDS = (
    'team_id', 'warn_value', 'warn_for', 'warn_keep_firing_for',
    'error_value', 'error_for', 'error_keep_firing_for', 'ttl', 'ttl_state',
    'expression', 'is_remote', 'trigger_type', 'desc', 'mute_new_metrics',
    'trigger_source', 'cluster_id', 'alone_metrics',
)

# Fields that are combined into the single ``sched`` trigger attribute.
SCHEDULE_FIELDS = (
    'start_hour', 'start_minute', 'end_hour', 'end_minute',
    'timezone_offset', 'disabled_days',
)


def get_schedule_days(disabled_days):
    '''Build the per-day schedule entries.

    Args:
        disabled_days (set): days with alerts disabled.

    Returns:
        list: schedule day entries.

    '''

    return [
        {'enabled': day not in disabled_days, 'name': day}
        for day in DAYS_OF_WEEK
    ]


def get_schedule(start_hour, start_minute, end_hour, end_minute, disabled_days, timezone_offset):
    days = get_schedule_days(disabled_days)
    return {
        'days': days,
        'startOffset': start_hour * MINUTES_IN_HOUR + start_minute,
        'endOffset': end_hour * MINUTES_IN_HOUR + end_minute,
        'tzOffset': timezone_offset,
    }


def overlay_schedule(base_sched, defined):
    '''Overlay explicitly defined schedule subfields on an existing schedule.

    Only the subfields named in ``defined`` are changed; all other schedule
    attributes are taken from ``base_sched``. This is what makes partial
    schedule updates safe: setting only ``disabled_days`` must not reset an
    existing custom ``start_hour``/``end_hour`` back to the defaults.

    Args:
        base_sched (dict or None): the schedule currently stored in Moira.
        defined (dict): schedule subfield values explicitly provided by the
            caller (a subset of SCHEDULE_FIELDS).

    Returns:
        dict: the merged schedule.

    '''

    base = (dict(base_sched) if base_sched
            else get_schedule(0, 0, 23, 59, [], 0))

    if 'disabled_days' in defined:
        base['days'] = get_schedule_days(set(defined['disabled_days']))

    if 'start_hour' in defined or 'start_minute' in defined:
        base_start = base.get('startOffset', 0)
        hour = defined.get('start_hour', base_start // MINUTES_IN_HOUR)
        minute = defined.get('start_minute', base_start % MINUTES_IN_HOUR)
        base['startOffset'] = hour * MINUTES_IN_HOUR + minute

    if 'end_hour' in defined or 'end_minute' in defined:
        base_end = base.get('endOffset', 23 * MINUTES_IN_HOUR + 59)
        hour = defined.get('end_hour', base_end // MINUTES_IN_HOUR)
        minute = defined.get('end_minute', base_end % MINUTES_IN_HOUR)
        base['endOffset'] = hour * MINUTES_IN_HOUR + minute

    if 'timezone_offset' in defined:
        base['tzOffset'] = defined['timezone_offset']

    return base


def validate_trigger_definition(trigger):
    '''Validate that an explicitly declared trigger type is consistent.

    Only fields that are actually being applied are checked, so a partial
    update that leaves other attributes untouched is never rejected.

    Args:
        trigger (dict): trigger preimage with the fields to be applied.

    Returns:
        An error message string if the definition is invalid, None otherwise.

    '''

    trigger_type = trigger.get('trigger_type')

    if trigger_type == 'expression':
        if 'expression' in trigger and not trigger.get('expression'):
            return ("trigger_type 'expression' requires a non-empty "
                    "'expression'")
    elif trigger_type in ('rising', 'falling'):
        missing = [field for field in ('warn_value', 'error_value')
                   if field not in trigger or trigger.get(field) is None]
        if missing:
            return ("trigger_type '%s' requires %s to be set" %
                    (trigger_type, ' and '.join(missing)))

    return None


def render_response_body(body):
    '''Render a (possibly non-JSON) API response body for diagnostics.

    Returns:
        Parsed JSON when possible, decoded text when the body is not JSON,
        and None when there is nothing to show.

    '''

    if body is None:
        return None
    if isinstance(body, (bytes, bytearray)):
        body = body.decode('utf-8', 'replace')
    if isinstance(body, str):
        try:
            return json.loads(body)
        except ValueError:
            return body
    return body


def handle_exception(function):
    '''Handling occurred exceptions.

    Returns:
        Default function JSON result on success,
        JSON with diagnostic info otherwise.

    The moira client raises MoiraApiError on HTTP errors and
    InvalidJSONError/ResponseStructureError on malformed responses. Older
    versions raised requests' HTTPError, so it is handled as well.

    '''

    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except HTTPError as occurred:
            response = getattr(occurred, 'response', None)
            return {
                'failed': {
                    'method': function.__name__,
                    'error': occurred.__class__.__name__,
                    'response_text': render_response_body(
                        getattr(response, 'text', None))
                }
            }
        except MoiraApiError as occurred:
            return {
                'failed': {
                    'method': function.__name__,
                    'error': occurred.__class__.__name__,
                    'response_text': render_response_body(
                        getattr(occurred, 'body', None))
                }
            }
        except (InvalidJSONError, ResponseStructureError) as occurred:
            return {
                'failed': {
                    'method': function.__name__,
                    'error': occurred.__class__.__name__,
                    'details': str(getattr(occurred, 'content', occurred))
                }
            }
        except Exception as occurred:
            return {
                'failed': {
                    'method': function.__name__,
                    'error': occurred.__class__.__name__,
                    'details': str(occurred),
                    'traceback': traceback.format_exc()
                }
            }

    return wrapper


class MoiraTrigger(object):
    '''Moira trigger.

    Args:
        trigger preimage (dict): trigger preimage.

    Attributes:
        client (moira_client.Client): moira client.
        preimage (dict): trigger preimage.

    '''

    def __init__(self, client, trigger_preimage):
        self.client = client
        self._id = trigger_preimage['id']
        self.preimage = trigger_preimage

    def has_image(self):
        '''Check if image exists.

        Returns:
            True if found, False otherwise.

        '''

        self.image = self.client.trigger.fetch_by_id(
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

        if 'tags' in self.preimage:
            self.preimage['tags'].sort()
            image.tags.sort()

        for field in ('name', 'desc'):
            if field in self.preimage and \
                    isinstance(self.preimage[field], bytes):
                self.preimage[field] = self.preimage[field].decode("utf-8")

        sched_defined = self.preimage.get('_sched_defined')

        for field in self.preimage:
            if field == 'id' or field == '_sched_defined':
                continue
            if field == 'sched' and sched_defined is not None:
                continue
            if image.__dict__.get(field) != self.preimage[field]:
                image.__dict__[field] = self.preimage[field]
                score += 1

        if sched_defined is not None:
            target = overlay_schedule(image.sched, sched_defined)
            if target != image.sched:
                image.sched = target
                score += 1

        return score != 0


class MoiraTriggerManager(object):
    '''Create, edit and delete Moira triggers.

    Args:
        client (moira_client.Client): moira client.
        dry_run (bool): enables check mode.

    '''

    def __init__(self, client, dry_run):
        self.client = client
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

        # Report the change regardless of dry_run and ignore the deletion
        # return value: TriggerManager.delete() inverts its result in the
        # moira-python-client, so it cannot be trusted.
        self.has_diff = True
        if not self.dry_run:
            self.client.trigger.delete(moira_trigger._id)

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
        result = {}
        if not moira_trigger.has_image():
            msg = 'trigger has been created'
            self.has_diff = True

            if not self.dry_run:
                preimage = moira_trigger.preimage.copy()
                preimage.pop('_sched_defined', None)
                trigger = self.client.trigger.create(**preimage)
                response = trigger.save()
                if response.get('checkResult'):
                    result['WARN'] = response['checkResult']

        else:
            trigger = moira_trigger.image

            if moira_trigger.merge_with(trigger):
                self.has_diff = True
                msg = 'trigger has been updated'

                if not self.dry_run:
                    response = trigger.update()
                    if response.get('checkResult'):
                        result['WARN'] = response['checkResult']
            else:
                msg = 'trigger has not been updated, it is already consistent'

        result[moira_trigger._id] = msg

        return result

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


def build_preimage(params, defined_fields):
    '''Build a trigger preimage from module parameters.

    Args:
        params (dict): module parameters.
        defined_fields (iterable): names of the fields the caller explicitly
            provided. When non-empty only these fields are applied (partial
            merge); an empty value keeps the legacy full-spec behaviour.

    Returns:
        dict: the trigger preimage.

    '''

    defined = set(defined_fields or [])
    partial = bool(defined)

    preimage = {'id': params['id']}

    for field in ('name', 'targets', 'tags') + OPTIONAL_FIELDS:
        if not partial or field in defined:
            value = params[field]
            # Without a value the client would infer the trigger type on
            # creation, so an unset trigger_type must never be compared with
            # (or sent to) the stored trigger: it is not a field the caller
            # controls until one is explicitly provided.
            if field == 'trigger_type' and value is None:
                continue
            preimage[field] = value

    if not partial and preimage.get('alone_metrics') is None:
        del preimage['alone_metrics']

    defined_sched = defined.intersection(SCHEDULE_FIELDS)
    if not partial:
        preimage['sched'] = get_schedule(
            params['start_hour'],
            params['start_minute'],
            params['end_hour'],
            params['end_minute'],
            set(params['disabled_days']),
            params['timezone_offset']
        )
    elif defined_sched:
        # A brand new trigger still needs a complete schedule, so a full one
        # is always built from the caller's values (defaults fill the rest).
        # ``_sched_defined`` tells the merge to only touch the explicitly
        # declared subfields of an existing schedule instead of replacing it.
        preimage['sched'] = get_schedule(
            params['start_hour'],
            params['start_minute'],
            params['end_hour'],
            params['end_minute'],
            set(params['disabled_days']),
            params['timezone_offset']
        )
        preimage['_sched_defined'] = {
            field: params[field]
            for field in SCHEDULE_FIELDS if field in defined_sched
        }

    return preimage


def main():
    '''Interact with Moira API via Ansible.

    '''

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
            'default': None,
            'no_log': True},
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
            'required': True},
        'team_id': {
            'type': 'str',
            'required': False,
            'default': None},
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
        'warn_keep_firing_for': {
            'type': 'int',
            'required': False,
            'default': None},
        'warn_for': {
            'type': 'int',
            'required': False,
            'default': None},
        'error_value': {
            'type': 'float',
            'required': False,
            'default': None},
        'error_for': {
            'type': 'int',
            'required': False,
            'default': None},
        'error_keep_firing_for': {
            'type': 'int',
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
            'choices': ['NODATA', 'DEL', 'ERROR', 'WARN', 'OK'],
            'default': 'NODATA'},
        'is_remote': {
            'type': 'bool',
            'required': False,
            'default': False},
        'trigger_source': {
            'type': 'str',
            'required': False,
            'choices': ['graphite_local', 'graphite_remote', 'prometheus_remote']},
        'cluster_id': {
            'type': 'str',
            'required': False,
            'default': None},
        'desc': {
            'type': 'str',
            'required': False,
            'default': ''},
        'mute_new_metrics': {
            'type': 'bool',
            'required': False,
            'default': False,
        },
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
            'default': 59},
        'alone_metrics': {
            'type': 'dict',
            'required': False,
            'default': None},
        'defined_fields': {
            'type': 'list',
            'required': False,
            'default': []},
    }

    module = AnsibleModule(
        argument_spec=fields,
        supports_check_mode=True)

    # When the caller lists the fields it provided, apply only those and leave
    # every other trigger attribute untouched (partial merge). Direct module
    # invocations without ``defined_fields`` keep the legacy full-spec
    # behaviour.
    preimage = build_preimage(
        module.params, module.params.get('defined_fields') or [])

    if module.params['state'] == 'present':
        validation_error = validate_trigger_definition(preimage)
        if validation_error is not None:
            module.fail_json(msg=validation_error)

    if not HAS_MOIRA_CLIENT:
        module.fail_json(msg=MISSING_MOIRA_CLIENT)

    api_client = Moira(
        api_url=module.params['api_url'],
        auth_custom=module.params['auth_custom'],
        auth_user=module.params['auth_user'],
        auth_pass=module.params['auth_pass'],
        login=module.params['login'])

    manager = MoiraTriggerManager(client=api_client, dry_run=module.check_mode)
    trigger = MoiraTrigger(client=api_client, trigger_preimage=preimage)

    result = manager.define_state(
        state=module.params['state'], moira_trigger=trigger)

    if 'failed' in result:
        module.fail_json(msg='Unable to define trigger state', meta=result)

    else:
        module.exit_json(changed=manager.has_diff, result=result)


if __name__ == '__main__':
    main()
