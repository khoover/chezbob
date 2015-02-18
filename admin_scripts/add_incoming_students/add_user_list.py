#!/usr/bin/python
import sys
import os
import pexpect

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
child = pexpect.spawn('ssh soda')
child.expect('@soda:')
child.sendline('psql -U bob')
for name,email in d.iteritems():

    child.expect('bob=>')
    child.sendline("insert into users (userid, username, email) values (nextval('userid_seq'), '" + name + "', '" + email + "');")
    i = child.expect(['ERROR','INSERT 0 1'])
    if i == 0:
        failed.append(email)
        print 'Failure on user: ' + email
        print child.before
    elif i == 1:
        succeeded.append(email)
    else:
        print 'wtf happened on user: ' + email
        print child.before

child.expect('bob=>')
child.sendline('\q')
child.expect('@soda:')
child.sendline('exit')
child.kill(0)

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
