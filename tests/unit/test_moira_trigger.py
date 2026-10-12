'''Unit tests for the moira_trigger Ansible module.

The module is imported with dummy replacements for ``ansible`` and
``moira_client`` so the tests run without a real Ansible installation or a
Moira API server.

'''

import importlib.util
import os
import sys
import types

import pytest

TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(TESTS_DIR)
MODULE_PATH = os.path.join(ROOT_DIR, 'library', 'moira_trigger.py')


def _stub_ansible():
    ansible = types.ModuleType('ansible')
    module_utils = types.ModuleType('ansible.module_utils')
    basic = types.ModuleType('ansible.module_utils.basic')

    class AnsibleModule:
        params = {}

        def __init__(self, *args, **kwargs):
            self.argument_spec = kwargs.get('argument_spec', {})
            self.supports_check_mode = kwargs.get('supports_check_mode', False)
            self.check_mode = False
            self.params = dict(AnsibleModule.params)

        def fail_json(self, **kwargs):
            raise AssertionError('module.fail_json(): %s' % kwargs)

        def exit_json(self, **kwargs):
            raise AssertionError('module.exit_json(): %s' % kwargs)

    basic.AnsibleModule = AnsibleModule
    ansible.module_utils = module_utils
    module_utils.basic = basic
    sys.modules['ansible'] = ansible
    sys.modules['ansible.module_utils'] = module_utils
    sys.modules['ansible.module_utils.basic'] = basic


def _stub_moira_client():
    moira = types.ModuleType('moira_client')
    client = types.ModuleType('moira_client.client')

    class Moira(object):
        def __init__(self, *args, **kwargs):
            pass

    class HTTPError(Exception):
        def __init__(self, response=None):
            self.response = response

    class MoiraApiError(Exception):
        def __init__(self, body):
            self.body = body

    class InvalidJSONError(Exception):
        def __init__(self, content, message=''):
            self.content = content
            self.message = message

    class ResponseStructureError(Exception):
        def __init__(self, message='', content=None):
            self.message = message
            self.content = content

    moira.Moira = Moira
    moira.HTTPError = HTTPError
    client.MoiraApiError = MoiraApiError
    client.InvalidJSONError = InvalidJSONError
    client.ResponseStructureError = ResponseStructureError
    sys.modules['moira_client'] = moira
    sys.modules['moira_client.client'] = client


@pytest.fixture(scope='session')
def mod():
    _stub_ansible()
    _stub_moira_client()
    spec = importlib.util.spec_from_file_location('moira_trigger', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    yield module
    sys.modules.pop('moira_trigger', None)
    for name in ('ansible', 'ansible.module_utils',
                 'ansible.module_utils.basic', 'moira_client',
                 'moira_client.client'):
        sys.modules.pop(name, None)


class FakeImage(object):
    '''Remote representation of a trigger returned by fetch_by_id.'''

    def __init__(self, store, data):
        self.__dict__.update(data)
        self._store = store

    def update(self):
        self._store.pushed.append(dict(self.__dict__))
        self._store.updated.append(self.__dict__.get('id'))
        return {'id': self.__dict__.get('id'), 'checkResult': ''}


class FakeTrigger(object):
    '''Locally built trigger returned by TriggerManager.create().'''

    def __init__(self, store, data):
        self.__dict__.update(data)
        self._store = store

    def save(self):
        self._store.saved.append(dict(self.__dict__))
        return {'id': self.__dict__.get('id'), 'checkResult': ''}


class FakeTriggerStore(object):
    def __init__(self, existing=None):
        self.existing = dict(existing or {})
        self.created = []
        self.updated = []
        self.deleted = []
        self.saved = []
        self.pushed = []

    def fetch_by_id(self, trigger_id):
        data = self.existing.get(trigger_id)
        if data is None:
            return None
        return FakeImage(self, data)

    def create(self, **preimage):
        self.created.append(preimage)
        return FakeTrigger(self, preimage)

    def delete(self, trigger_id):
        self.deleted.append(trigger_id)
        # The moira-python-client inverts the delete result on success
        return False


class FakeClient(object):
    def __init__(self, store):
        self.trigger = store


def full_params(**overrides):
    params = {
        'id': 'trigger-1',
        'team_id': None,
        'name': 'Trigger 1',
        'targets': ['prefix.metric.p1'],
        'tags': ['TAG'],
        'warn_value': 300,
        'warn_for': 60,
        'warn_keep_firing_for': None,
        'error_value': 600,
        'error_for': 60,
        'error_keep_firing_for': None,
        'ttl': 600,
        'ttl_state': 'NODATA',
        'expression': 't1 > 600',
        'is_remote': False,
        'trigger_type': None,
        'desc': '',
        'mute_new_metrics': False,
        'trigger_source': None,
        'cluster_id': None,
        'alone_metrics': None,
        'disabled_days': ['Mon'],
        'timezone_offset': 0,
        'start_hour': 0,
        'start_minute': 0,
        'end_hour': 23,
        'end_minute': 59,
    }
    params.update(overrides)
    return params


def present(mod, store, preimg, dry_run=False):
    client = FakeClient(store)
    manager = mod.MoiraTriggerManager(client=client, dry_run=dry_run)
    trigger = mod.MoiraTrigger(client=client, trigger_preimage=preimg)
    result = manager.define_state('present', trigger)
    return manager, result


def absent(mod, store, preimg, dry_run=False):
    client = FakeClient(store)
    manager = mod.MoiraTriggerManager(client=client, dry_run=dry_run)
    trigger = mod.MoiraTrigger(client=client, trigger_preimage=preimg)
    result = manager.define_state('absent', trigger)
    return manager, result


# ---------------------------------------------------------------------------
# build_preimage


def test_build_preimage_full(mod):
    pre = mod.build_preimage(full_params(), [])
    assert pre['id'] == 'trigger-1'
    for field in ('name', 'targets', 'tags', 'warn_value', 'warn_for',
                  'error_value', 'ttl', 'expression', 'desc'):
        assert field in pre
    assert 'sched' in pre
    assert 'alone_metrics' not in pre


def test_build_preimage_alone_metrics_only_when_set(mod):
    pre = mod.build_preimage(
        full_params(alone_metrics={'some': {'value': '> 0'}}), [])
    assert pre['alone_metrics'] == {'some': {'value': '> 0'}}


def test_build_preimage_partial_basic(mod):
    pre = mod.build_preimage(full_params(), ['name', 'tags'])
    assert set(pre.keys()) == {'id', 'name', 'tags'}
    assert 'sched' not in pre
    assert 'targets' not in pre


def test_build_preimage_partial_schedule(mod):
    pre = mod.build_preimage(full_params(), ['disabled_days'])
    assert 'sched' in pre
    assert pre['_sched_defined'] == {'disabled_days': ['Mon']}


def test_build_preimage_partial_schedule_partial_set(mod):
    pre = mod.build_preimage(
        full_params(), ['disabled_days', 'start_hour'])
    assert pre['_sched_defined'] == {
        'disabled_days': ['Mon'], 'start_hour': 0}


def test_build_preimage_skips_trigger_type_when_unset(mod):
    pre = mod.build_preimage(full_params(), [])
    assert 'trigger_type' not in pre


def test_build_preimage_keeps_trigger_type_when_set(mod):
    pre = mod.build_preimage(full_params(trigger_type='expression'), [])
    assert pre['trigger_type'] == 'expression'


def test_build_preimage_schedule_layout(mod):
    pre = mod.build_preimage(full_params(disabled_days=['Mon']), [])
    sched = pre['sched']
    assert sched['startOffset'] == 0
    assert sched['endOffset'] == 23 * 60 + 59
    assert sched['tzOffset'] == 0
    assert len(sched['days']) == 7
    by_name = {day['name']: day for day in sched['days']}
    assert by_name['Mon']['enabled'] is False
    assert by_name['Tue']['enabled'] is True


# ---------------------------------------------------------------------------
# validate_trigger_definition


def test_validate_expression_requires_expression(mod):
    pre = mod.build_preimage(
        full_params(trigger_type='expression', expression=''), [])
    assert mod.validate_trigger_definition(pre) is not None


def test_validate_expression_ok(mod):
    pre = mod.build_preimage(
        full_params(trigger_type='expression', expression='t1 > 600'), [])
    assert mod.validate_trigger_definition(pre) is None


def test_validate_rising_requires_values(mod):
    pre = mod.build_preimage(
        full_params(trigger_type='rising', warn_value=None,
                    error_value=None), [])
    assert mod.validate_trigger_definition(pre) is not None


def test_validate_rising_ok(mod):
    pre = mod.build_preimage(
        full_params(trigger_type='rising', warn_value=300, error_value=600),
        [])
    assert mod.validate_trigger_definition(pre) is None


def test_validate_falling_missing_error_value(mod):
    pre = mod.build_preimage(
        full_params(trigger_type='falling', warn_value=300,
                    error_value=None), [])
    assert mod.validate_trigger_definition(pre) is not None


def test_validate_partial_trigger_type_is_checked(mod):
    pre = mod.build_preimage(full_params(warn_value=None, error_value=None),
                             ['trigger_type', 'name'])
    pre['trigger_type'] = 'rising'
    assert mod.validate_trigger_definition(pre) is not None


# ---------------------------------------------------------------------------
# render_response_body


def test_render_response_body(mod):
    assert mod.render_response_body(None) is None
    assert mod.render_response_body(b'{"a": 1}') == {'a': 1}
    assert mod.render_response_body('{"b": 2}') == {'b': 2}
    assert mod.render_response_body(b'not json') == 'not json'
    assert mod.render_response_body(42) == 42


# ---------------------------------------------------------------------------
# present: create


def test_present_create(mod):
    store = FakeTriggerStore()
    manager, result = present(
        mod, store, mod.build_preimage(full_params(), []))
    assert manager.has_diff is True
    assert len(store.created) == 1
    assert len(store.saved) == 1
    assert result['trigger-1'] == 'trigger has been created'


def test_present_create_check_mode(mod):
    store = FakeTriggerStore()
    manager, _ = present(
        mod, store, mod.build_preimage(full_params(), []), dry_run=True)
    assert manager.has_diff is True
    assert store.created == []
    assert store.saved == []


# ---------------------------------------------------------------------------
# present: update


def test_present_update(mod):
    pre = mod.build_preimage(full_params(), [])
    existing = dict(pre)
    existing['desc'] = 'old description'
    store = FakeTriggerStore(existing={pre['id']: existing})
    manager, result = present(mod, store, pre)
    assert manager.has_diff is True
    assert store.updated == ['trigger-1']
    assert result['trigger-1'] == 'trigger has been updated'


def test_present_update_idempotent(mod):
    pre = mod.build_preimage(full_params(), [])
    store = FakeTriggerStore(existing={pre['id']: dict(pre)})
    manager, result = present(mod, store, pre)
    assert manager.has_diff is False
    assert store.updated == []
    assert 'already consistent' in result['trigger-1']


def test_present_update_check_mode(mod):
    pre = mod.build_preimage(full_params(), [])
    existing = dict(pre)
    existing['desc'] = 'old description'
    store = FakeTriggerStore(existing={pre['id']: existing})
    manager, _ = present(mod, store, pre, dry_run=True)
    assert manager.has_diff is True
    assert store.updated == []


def test_present_update_unset_trigger_type_ignored(mod):
    pre = mod.build_preimage(full_params(), [])
    existing = dict(mod.build_preimage(full_params(), []))
    existing['trigger_type'] = 'rising'
    store = FakeTriggerStore(existing={pre['id']: existing})
    manager, result = present(mod, store, pre)
    assert manager.has_diff is False
    assert store.updated == []
    assert 'already consistent' in result['trigger-1']


def test_present_update_applies_declared_trigger_type(mod):
    pre = mod.build_preimage(
        full_params(trigger_type='rising', warn_value=300, error_value=600),
        [])
    existing = dict(mod.build_preimage(full_params(), []))
    existing['trigger_type'] = 'expression'
    store = FakeTriggerStore(existing={pre['id']: existing})
    manager, result = present(mod, store, pre)
    assert manager.has_diff is True
    assert store.updated == ['trigger-1']
    assert result['trigger-1'] == 'trigger has been updated'
    assert store.pushed[-1]['trigger_type'] == 'rising'


def test_present_partial_trigger_type_only_change_is_applied(mod):
    pre = mod.build_preimage(
        full_params(trigger_type='expression', expression='t1 > 600'),
        ['id', 'name', 'trigger_type'])
    existing = dict(mod.build_preimage(
        full_params(trigger_type='rising', warn_value=300, error_value=600),
        []))
    store = FakeTriggerStore(existing={pre['id']: existing})
    manager, result = present(mod, store, pre)
    assert manager.has_diff is True
    assert store.updated == ['trigger-1']
    assert result['trigger-1'] == 'trigger has been updated'
    assert store.pushed[-1]['trigger_type'] == 'expression'


# ---------------------------------------------------------------------------
# absent: remove


def test_absent_remove(mod):
    pre = mod.build_preimage(full_params(), [])
    store = FakeTriggerStore(existing={pre['id']: dict(pre)})
    manager, result = absent(mod, store, pre)
    assert manager.has_diff is True
    assert store.deleted == ['trigger-1']
    assert result['trigger-1'] == 'trigger has been removed'


def test_absent_missing(mod):
    pre = mod.build_preimage(full_params(), [])
    store = FakeTriggerStore()
    manager, result = absent(mod, store, pre)
    assert manager.has_diff is False
    assert store.deleted == []
    assert result['trigger-1'] == 'no id found for trigger'


def test_absent_check_mode(mod):
    pre = mod.build_preimage(full_params(), [])
    store = FakeTriggerStore(existing={pre['id']: dict(pre)})
    manager, _ = absent(mod, store, pre, dry_run=True)
    assert manager.has_diff is True
    assert store.deleted == []


# ---------------------------------------------------------------------------
# partial merge through the manager


def test_present_partial_update_keeps_other_fields(mod):
    pre = mod.build_preimage(full_params(desc='new desc'),
                             ['id', 'name', 'desc'])
    existing = dict(mod.build_preimage(full_params(desc='old desc'), []))
    store = FakeTriggerStore(existing={pre['id']: existing})
    manager, _ = present(mod, store, pre)
    assert manager.has_diff is True
    assert store.updated == ['trigger-1']


def test_present_partial_disabled_days_preserves_schedule_fields(mod):
    pre = mod.build_preimage(full_params(disabled_days=['Mon', 'Wed']),
                             ['id', 'name', 'disabled_days'])
    existing = dict(mod.build_preimage(
        full_params(start_hour=9, end_hour=17, timezone_offset=-180), []))
    store = FakeTriggerStore(existing={pre['id']: existing})
    manager, _ = present(mod, store, pre)
    assert manager.has_diff is True
    assert store.updated == ['trigger-1']
    sched = store.pushed[-1]['sched']
    assert sched['startOffset'] == 9 * 60
    assert sched['endOffset'] == 17 * 60 + 59
    assert sched['tzOffset'] == -180
    by_name = {day['name']: day for day in sched['days']}
    assert by_name['Mon']['enabled'] is False
    assert by_name['Wed']['enabled'] is False
    assert by_name['Tue']['enabled'] is True


def test_present_partial_schedule_idempotent(mod):
    pre = mod.build_preimage(full_params(disabled_days=['Mon']),
                             ['id', 'name', 'disabled_days'])
    existing = dict(mod.build_preimage(full_params(disabled_days=['Mon']), []))
    store = FakeTriggerStore(existing={pre['id']: existing})
    manager, result = present(mod, store, pre)
    assert manager.has_diff is False
    assert store.updated == []
    assert 'already consistent' in result['trigger-1']


def test_present_partial_schedule_create_uses_complete_schedule(mod):
    pre = mod.build_preimage(full_params(disabled_days=['Mon']),
                             ['id', 'name', 'disabled_days'])
    store = FakeTriggerStore()
    manager, _ = present(mod, store, pre)
    assert manager.has_diff is True
    assert len(store.created) == 1
    assert '_sched_defined' not in store.created[0]
    sched = store.created[0]['sched']
    assert sched['startOffset'] == 0
    assert sched['endOffset'] == 23 * 60 + 59
    assert sched['tzOffset'] == 0
    assert len(sched['days']) == 7


# ---------------------------------------------------------------------------
# error handling


class _Response(object):
    text = '{"message": "not found"}'


def test_error_http_error(mod):
    store = FakeTriggerStore()

    def boom(trigger_id):
        raise mod.HTTPError(_Response())

    store.fetch_by_id = boom
    pre = mod.build_preimage(full_params(), [])
    _, result = present(mod, store, pre)
    assert 'failed' in result
    assert result['failed']['error'] == 'HTTPError'
    assert result['failed']['response_text'] == {'message': 'not found'}


def test_error_moira_api_error(mod):
    store = FakeTriggerStore()

    def boom(trigger_id):
        raise mod.MoiraApiError('{"error": "boom"}')

    store.fetch_by_id = boom
    pre = mod.build_preimage(full_params(), [])
    _, result = present(mod, store, pre)
    assert 'failed' in result
    assert result['failed']['error'] == 'MoiraApiError'
    assert result['failed']['response_text'] == {'error': 'boom'}


def test_error_invalid_json(mod):
    store = FakeTriggerStore()

    def boom(trigger_id):
        raise mod.InvalidJSONError('<html>')

    store.fetch_by_id = boom
    pre = mod.build_preimage(full_params(), [])
    _, result = present(mod, store, pre)
    assert 'failed' in result
    assert result['failed']['error'] == 'InvalidJSONError'


def test_error_unexpected_exception_has_traceback(mod):
    store = FakeTriggerStore()

    def boom(trigger_id):
        raise ValueError('boom')

    store.fetch_by_id = boom
    pre = mod.build_preimage(full_params(), [])
    _, result = present(mod, store, pre)
    assert 'failed' in result
    assert result['failed']['error'] == 'ValueError'
    assert 'details' in result['failed']
    assert result['failed']['traceback'].startswith('Traceback')