#!/usr/bin/python
import sys
import os
import subprocess

command = './add_user'

# open the file
if len(sys.argv) != 2:
    print 'Correct usage: ./add_user_list.py list_of_names'
    sys.exit(0)
if not (os.path.isfile(sys.argv[1])):
    print sys.argv[1] + ' is not a file'
    sys.exit(0)
f = open(sys.argv[1],'r')

# generate dictionary of names and emails
d = {}
for line in f:
    email = line.strip()
    if (1==0): # check the email address
        print email + ' is not a valid email address'
        sys.exit(0)
    name = email.split('@')[0]
    if name in d: # check for duplicates
        print 'ERROR: duplicate user ' + name
	sys.exit(0)
    d[name] = email

# add the new users
failed = []
succeeded = []
for name,email in d.iteritems():
    args=[command,name,email]
    output = subprocess.check_output(args,shell=False)
    if 'SUCCESS' not in output:
        print 'Failure on user: ' + name + ', ' + email
        print 'Output is as follows:'
        print output
        failed.append(email)
    else:
        succeeded.append(email)

# determine the success of the operation
if len(failed) == 0:
    print 'Great success!'
else:
    print '---- Succeeded on these users ----'
    for user in succeeded:
        print user
    print ''
    print '---- Failed on these users ----'
    for user in failed:
        print user
f.close()
