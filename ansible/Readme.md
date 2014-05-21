#Ansible

Ansible is used to configure machines. We currently use it to setup soda, although chezbob should also be moved to Ansible.

#Setup

Make sure the 'externals/ansible' submodule is checked out:

    $ git submodule update externals/ansible

Then run:

    $ source configure_ansible
    $ ansible-playbook site.yml -kK

To deploy/update the machines.


