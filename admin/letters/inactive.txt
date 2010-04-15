# Query: select username, email, balance from users natural join balances natural left join last_activity where balance > 0 and (time is null or time < '2007-01-01') order by balance, lower(username);
# Fields: USERNAME EMAIL BALANCE
From: Chez Bob <chezbob@cs.ucsd.edu>
Subject: Your Chez Bob Account: %USERNAME%

| Chez Bob, the UCSD CSE grad student food co-op, has been sorting
| through old accounts.  According to our records, you have an account
| with Chez Bob--%USERNAME%--which has not been used in quite some time.
| This account currently has a balance of %BALANCE%.

| You may let us know if you would like to keep the account open; we are
| happy to do so.  If you are no longer associated with the department
| or otherwise wish to close your account, please let us know by
| replying to this e-mail or to mvrable@cs.ucsd.edu, the current finance
| manager.

| If closing your account, you have the option of donating your
| remaining balance to Chez Bob or transferring the balance to another
| user's account--at the current time, Chez Bob is not sending out
| balance refunds.  If requesting your account be closed, please let us
| know how you would like your remaining balance to be handled.

--Chez Bob
