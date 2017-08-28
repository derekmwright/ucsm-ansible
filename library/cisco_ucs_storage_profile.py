#!/usr/bin/env python

from ansible.module_utils.basic import *

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}



DOCUMENTATION = '''
---
module: cisco_ucs_storage_profile
short_description: configures storage profiles on cisco ucs manager
version_added: 0.9.0.0
description:
   -  configures storage profiles on cisco ucs manager
options:
    storage_profile:
        description: storage_profile dictionary
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
  cisco_ucs_storage_profile:
    storage_profile:
      name: Docker-StgProf
    ucs_ip: "192.168.1.1"
    ucs_username: "admin"
    ucs_password: "password"
'''


def _argument_mo():
    return dict(
                storage_profile=dict(required=True, type='dict'),
                org_dn=dict(type='str', default="org-root"),
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


def setup_storage_profile(server, module):
    from ucsmsdk.mometa.lstorage.LstorageProfile import LstorageProfile
    from ucsmsdk.mometa.lstorage.LstorageDasScsiLun import LstorageDasScsiLun
   
    ansible = module.params
    args_mo  =  _get_mo_params(ansible)

    mo = server.query_dn(args_mo['org_dn']+'/profile-'+args_mo['storage_profile']['name'])
    if mo:
        exists = True
    else:
        exists = False

    if module.check_mode or exists:
        return not exists
       
    mo = LstorageProfile(parent_mo_or_dn=args_mo['org_dn'],
                         name=args_mo['storage_profile']['name'])
    if(len(args_mo['storage_profile']['lun_list']) <> 0 ):
        for lun in args_mo['storage_profile']['lun_list'] :
            mo_1 = LstorageDasScsiLun(parent_mo_or_dn=mo,
	                              local_disk_policy_name=lun['disk_group_policy'],
				      name=lun['lun_name'],
				      size=lun['size'])
    server.add_mo(mo, True)
    server.commit()
    return True


def setup(server, module):
    result = {}
    err = False

    try:
        result["changed"] = setup_storage_profile(server, module)
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
