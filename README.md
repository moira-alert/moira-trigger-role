[![Build Status](https://travis-ci.org/moira-alert/moira-trigger-role.svg?branch=master)](https://travis-ci.org/moira-alert/moira-trigger-role)

# moira-trigger-role

Ansible role to create, update and delete Moira triggers based on
[python-moira-client](https://github.com/moira-alert/python-moira-client)

## Role usage

[Installation](#installation)
-   [Ansible Galaxy](#ansible-galaxy)
-   [Git clone](#git-clone)

[Configuration](#configuration)
-   [Authentication](#authentication)
-   [Trigger state](#trigger-state)
-   [Role variables](#role-variables)

[Role tasks](#role-tasks)
-   [Manage dependencies](#manage-dependencies)
-   [Manage triggers](#manage-triggers)

## <a name="installation"></a> Installation

### <a name="ansible-galaxy"></a> Ansible Galaxy

```
ansible-galaxy install moira-alert.moira-trigger-role
```

### <a name="git-clone"></a> Git clone

Clone this repository into your roles directory:

```
cd /etc/ansible/roles && rolepath=moira-alert.moira-trigger-role
git clone https://github.com/moira-alert/moira-trigger-role $rolepath
```

## <a name="configuration"></a> Configuration

### <a name="authentication"></a> Authentication

Authentication parameters can be specified inside */defaults/main.yml*

| Parameter | Description | Type | Required | Default | Example |
| ------ | ------ | ------ | ------ | ------ | ------ |
| api_url | Url of Moira API | String | True | | <http://localhost/api/> |
| auth_custom | Custom authorization headers | Dictionary | False | None | Authorization: token |
| auth_user | Auth User (Basic Auth) | String | False | None | admin |
| auth_pass | Auth Password (Basic Auth) | String | False | None | pass |
| login | Auth Login (Basic Auth) | String | False | None | admin |

### <a name="trigger-state"></a> Trigger state

Trigger parameters can be defined inside */vars/main.yml*

| Parameter | Description | Type | Required | Choices | Default | Example |
| ------ | ------ | ------ | ------ | ------ | ------ | ------ |
| state | Desired state of a trigger | String | True | present <br> absent |  | present |
| id | Trigger id | String | True | | | trigger_1 |
| name | Trigger name | String | True | | | Trigger 1 |
| tags | List of trigger tags | List | True | | | - Project <br> - Service |
| targets | List of trigger targets <br> [See available graphite functions](https://github.com/go-graphite/carbonapi/blob/master/COMPATIBILITY.md#functions) | List | True | | | - prefix.*.postfix |
| warn_value | Value to set WARN status | Float | True | | None | 300 |
| error_value | Value to set ERROR status | Float | True | | None | 600 |
| ttl | Time to Live (in seconds) | Int | False | | 600 | 600 |
| ttl_state | Trigger state at the expiration of 'ttl' | String | False | NODATA <br> ERROR <br> WARN <br> OK | NODATA | WARN |
| desc | Trigger description | String | False | | | trigger test description |
| expression | [C-like expression](https://github.com/Knetic/govaluate) | String | False | | | t1 >= 10 ? ERROR : (t1 >= 1 ? WARN : OK) |
| disabled_days | Days for trigger to be in silent mode | Set | False | | | ? Mon <br> ? Wed |

> **Note:** By default, file contains examples of triggers with LoadAverage, MemoryFree and DiskSpace <br>
> targets of most commonly used [Diamond](https://github.com/python-diamond/Diamond) collectors

### <a name="role-variables"></a> Role variables

Next, pass following variables to role inside playbook:

| Variable | Description | Type | Required | Choices | Default | Example |
| ------ | ------ | ------ | ------ | ------ | ------ | ------ |
| dry_run | Run in check mode | Boolean | False | True <br> False | True |
| project | Graphite metric prefix | String | True | | | DevOps |
| service | Graphite metric | String | True | | | system |

```
- hosts: inventory_hostgroup
  vars:
    project: DevOps
    service: system
    dry_run: False
  roles:
   - moira-alert.moira_trigger-role
```

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
