# moira-trigger-role

If you're new here, better check out our main [README](https://github.com/moira-alert/moira/blob/master/README.md).

Ansible role to create, update and delete Moira triggers based on
[python-moira-client](https://github.com/moira-alert/python-moira-client)

## Role usage

[Installation](#installation)
-   [Ansible Galaxy](#ansible-galaxy)
-   [Ansible Role with Makefile](#ansible-role)

[Configuration](#configuration)
-   [Authentication](#authentication)
-   [Trigger state](#trigger-state)

[Role tasks](#role-tasks)
-   [Manage dependencies](#manage-dependencies)
-   [Manage triggers](#manage-triggers)

## <a name="installation"></a> Installation

### <a name="ansible-galaxy"></a> Ansible Galaxy

```
ansible-galaxy install moira-alert.moira-trigger-role
```

### <a name="ansible-role"></a> Ansible Role with Makefile

Place the contents from [example](https://github.com/moira-alert/moira-trigger-role/blob/master/tests/Makefile) inside your Makefile to download role from Ansible Galaxy <br>
and create playbook to manage triggers with predefined parameters inside your vars files:

```
- name: manage moira triggers
  hosts: serviceName
  roles:
    - role: moira-alert.moira-trigger-role
      moira_api: http://localhost:8081/api
      moira_triggers: '{{ ServiceNameTriggers }}'
      delegate_to: 127.0.0.1
      run_once: True
      dry_run: False
```

> **Note:** All tasks must be done from your ansible control machine

## <a name="configuration"></a> Configuration

Predefine following parameters inside your vars files. Working examples can be found [here](https://github.com/moira-alert/moira-trigger-role/tree/master/tests/group_vars)

### <a name="authentication"></a> Authentication

| Parameter | Description | Type | Required | Default | Example |
| ------ | ------ | ------ | ------ | ------ | ------ |
| moira_api | Url of Moira API | String | True | N/A | <http://localhost/api/> |
| moira_auth_custom | Custom authorization headers | Dictionary | False | None | Authorization: apiKey |
| moira_auth_user | Auth User (Basic Auth) | String | False | None | admin |
| moira_auth_pass | Auth Password (Basic Auth) | String | False | None | pass |
| moira_auth_login | Auth Login (Basic Auth) | String | False | None | admin |

> **Note:** Use moira_auth_custom if you're using additional authentication mechanisms instead of <br>
> single basic auth, use moira_auth_user, moira_auth_pass and moira_auth_login otherwise. <br>
> moira_auth_login must contain value for X-Webauth-User header.

### <a name="trigger-state"></a> Trigger state

| Parameter | Description | Type | Required | Choices | Default | Example |
| ------ | ------ | ------ | ------ | ------ | ------ | ------ |
| state | Desired state of a trigger | String | True | present <br> absent | N/A | present |
| id | Trigger id | String | True | N/A | N/A | trigger_1 |
| name | Trigger name | String | True | N/A | N/A | Trigger 1 |
| tags | List of trigger tags | List | True | N/A | N/A | - Project <br> - Service |
| targets | List of trigger targets <br> [See available graphite functions](https://github.com/go-graphite/carbonapi/blob/master/COMPATIBILITY.md#functions) | List | True | N/A | N/A | - prefix.*.postfix |
| warn_value | Value to set WARN status | Float | False | N/A | None | 300 |
| error_value | Value to set ERROR status | Float | False | N/A | None | 600 |
| trigger_type | Type of a trigger | String | False | rising <br> falling <br> expression | N/A | rising |
| expression | [C-like expression](https://github.com/Knetic/govaluate) | String | False | N/A | Empty string | t1 >= 10 ? ERROR : (t1 >= 1 ? WARN : OK) |
| ttl | Time to Live (in seconds) | Int | False | N/A | 600 | 600 |
| ttl_state | Trigger state at the expiration of 'ttl' | String | False | NODATA <br> DEL <br> ERROR <br> WARN <br> OK | NODATA | WARN |
| is_remote | Use remote storage | Bool | False | True <br> False | False | False |
| desc | Trigger description | String | False | N/A | Empty string | trigger test description |
| mute_new_metrics | Mute new metrics | Bool | False | True <br> False | False | False |
| disabled_days | Days for trigger to be in silent mode | List | False | N/A | Empty list | - Mon <br> - Wed |
| timezone_offset | Timezone offset (minutes) | Int | False | N/A | 0 | -180 |
| start_hour | Start hour to send alerts | Int | False | N/A | 0 | 9 |
| start_minute | Start minute to send alerts | Int | False | N/A | 0 | 0 |
| end_hour | End hour to send alerts | Int | False | N/A | 23 | 17 |
| end_minute | End minute to send alerts | Int | False | N/A | 59 | 0 |
| alone_metrics | Set some target as single metric | Object, example:  | False | N/A | {'t1': False, 't2': True, ... 'tN': True} | {'t1': False, 't2': False} |

## <a name="role-tasks"></a> Role tasks

### <a name="manage-dependencies"></a> Manage dependencies

Task to check [python-moira-client](https://github.com/moira-alert/python-moira-client) is  installed (via pip)

### <a name="manage-triggers"></a> Manage triggers

Use state 'present' to create and edit existing triggers:

```
 - name: create trigger
   moira_trigger:
      ...
      state: present
      ...  
```

To delete existing triggers use state 'absent':

```
 - name: remove trigger
   moira_trigger:
      ...
      state: absent
      ...  
```
