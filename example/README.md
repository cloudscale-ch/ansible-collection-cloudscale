# README

This is an example ansible project which shows how to build a multi zone setup on cloudscale.ch with two logical cloud environments: _prod_ and _stage_. Each zone may (or may not) use a different cloudscale.ch API token stored in a _secrets.yml_ (which is meant to be encrypted).

In our project, we defined a bunch of web and databases servers which will be grouped into an _server group_ for anti-affinity.

This setup could be easily extended to more cloud environments or even used as a green/blue deployment setup.

## Setup

```shell
python3 -m venv .venv
source ./venv/bin/activate
pip install -r requirements.txt
```

## Configure

Set your cloudscale.ch API token in _inventory/group_vars/stage/secrets.yml_ and _inventory/group_vars/prod/secrets.yml_.

## Create Stage Environment

```shell
ansible-playbook playbooks/cloud.yml -i inventory/stage-lpg1
```

## Create Prod Environments

```shell
ansible-playbook playbooks/cloud.yml -i inventory/prod-lpg1 -i inventory/prod-rma1
```
