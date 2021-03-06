#!/usr/bin/env python

from ansible.module_utils.basic import *

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}



DOCUMENTATION = '''
---
module: cisco_ucs_vhba_template
short_description: configures service profiles on cisco ucs manager
version_added: 0.9.0.0
description:
   -  configures service profiles on cisco ucs manager
options:
    state:
        description:
         - if C(present), will perform create/add/enable operation
         - if C(absent), will perform delete/remove/disable operation
        required: false
        choices: ['present', 'absent']
        default: 'present'
    vhba_list:
        description: list of vhba dictionaries
        required: true
    org_dn:
        description: org dn
        required: false
        default: "org-root"

requirements: ['ucsmsdk', 'ucsm_apis']
author: "Cisco Systems Inc(ucs-python@cisco.com)"
'''


EXAMPLES = '''
- name:
  cisco_ucs_vhba_template:
    vhba_list:
      - {"name":"DDC-DTR-1"...
    ucs_ip: "192.168.1.1"
    ucs_username: "admin"
    ucs_password: "password"
'''


def _argument_mo():
    return dict(
                vhba_list=dict(required=True, type='list'),
                org_dn=dict(type='str', default="org-root"),
    )

def _argument_custom():
    return dict(
        state=dict(default='present',
                   choices=['present', 'absent'],
                   type='str'),
    )

def _argument_connection():
    return  dict(
        # UcsHandle
        ucs_server=dict(type='dict'),

        # Ucs server credentials
        ucs_ip=dict(type='str'),
        ucs_username=dict(default="admin", type='str'),
        ucs_password=dict(type='str', no_log=True),
        ucs_port=dict(default=None),
        ucs_secure=dict(default=None),
        ucs_proxy=dict(default=None)
    )



def _ansible_module_create():
    argument_spec = dict()
    argument_spec.update(_argument_connection())
    argument_spec.update(_argument_mo())
    argument_spec.update(_argument_custom())

    return AnsibleModule(argument_spec,
                         supports_check_mode=True)



def _get_mo_params(params):
    from ansible.module_utils.cisco_ucs import UcsConnection
    args = {}
    for key in _argument_mo():
        if params.get(key) is None:
            continue
        args[key] = params.get(key)
    return args


def setup_vhba_template(server, module):
    from ucsmsdk.mometa.vnic.VnicSanConnTempl import VnicSanConnTempl
    from ucsmsdk.mometa.vnic.VnicFcIf import VnicFcIf
   
    ansible = module.params
    args_mo  =  _get_mo_params(ansible)

    changed = False

    for vhba in args_mo['vhba_list']:
        exists = False
        mo = server.query_dn(args_mo['org_dn']+'/san-conn-templ-'+vhba['name'])
        if mo:
            exists = True

        if ansible['state'] == 'absent':
            if exists:
                changed = True
                if not module.check_mode:
                    server.remove_mo(mo)
                    server.commit()
        else:
            if not exists:
                changed = True
                if not module.check_mode:
                    # create if mo does not already exist
	            mo = VnicSanConnTempl(parent_mo_or_dn=args_mo['org_dn'],
	                                  ident_pool_name=vhba['wwpn_pool'],
				          name=vhba['name'],
				          switch_id=vhba['fabric'])
	            mo_1 = VnicFcIf(parent_mo_or_dn=mo, name=vhba['vsan'])
                    server.add_mo(mo, True)
                    server.commit()

    return changed


def setup(server, module):
    result = {}
    err = False

    try:
        result["changed"] = setup_vhba_template(server, module)
    except Exception as e:
        err = True
        result["msg"] = "setup error: %s " % str(e)
        result["changed"] = False

    return result, err


def main():
    from ansible.module_utils.cisco_ucs import UcsConnection

    module = _ansible_module_create()
    conn = UcsConnection(module)
    server = conn.login()
    result, err = setup(server, module)
    conn.logout()
    if err:
        module.fail_json(**result)
    module.exit_json(**result)


if __name__ == '__main__':
    main()

