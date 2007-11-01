# bob_db.pl
#
# A set of routines that encapsulates the calls to the Postgres database 
# backend.  The routines are rather repetitive and not particularly 
# flexible, but it certainly makes the other code a lot simpler to read 
# and maintain.  Any future database calls should be placed in this module.
#
# It's worth remembering that strings in most databases (incl. Postgres)
# are delimited by single (') quotation marks/apostrophes.  The database
# will crash if you try inserting a string with an apostrophe.  Check out
# the 'esc_apos' function which looks for apostrophes in a string and 
# escapes them by adding a second apostrophe.
#
# 'Pg' is a Perl module that allows us to access a Postgres database.  
# Packages are available for both Redhat and Debian.

use Pg;
require "ctime.pl" unless defined &ctime;

my $conn = "";         			# the database connection    
my $ADMIN = 'chezbob@cs.ucsd.edu';    # address to send admin. message

$NOT_FOUND = -9999.9999;    

# Transactions are tagged with a source which indicates how the transaction was
# entered into the database.  Currently used sources are: "chezbob", "soda",
# and "socialhour".  This code defaults to "chezbob", but this can be
# overridden by called bob_db_set_source.
my $database_source = 'chezbob';
sub bob_db_set_source {
  my $source = shift;
  $database_source = $source || 'chezbob';
}

sub
bob_db_connect
{
  $conn = Pg::connectdb("dbname=bob");
  if ($conn->status == PGRES_CONNECTION_BAD) {
    my $mesg = "Error connecting to database.\n";
    $mesg .= $conn->errorMessage;
    &report_fatal($mesg);
  }
}


sub
bob_db_check_conn
{
  if ($conn->status != PGRES_CONNECTION_OK) {
    my $mesg = "Connection to Bob database lost.\n";
    &report_fatal($mesg);
  }
}

sub
bob_db_disconnect
{
    undef $conn;
}

sub
bob_db_xact_begin
{
  &bob_db_check_conn;
  my $result = $conn->exec("BEGIN;");
  if ($result->resultStatus != PGRES_COMMAND_OK) {
    &report_fatal("Error in bob_db_xact_begin\n");
  }
}

sub
bob_db_xact_commit
{
  &bob_db_check_conn;
  my $result = $conn->exec("COMMIT;");
  if ($result->resultStatus != PGRES_COMMAND_OK) {
    &report_fatal("Error in bob_db_xact_commit\n");
  }
}

#---------------------------------------------------------------------------
# users table

sub
bob_db_get_username_from_userbarcode
{
  my ($barcode) = @_;

  &bob_db_check_conn;
  my $queryFormat = q{
    select username
    from users
    where userbarcode = '%s';
  };
  my $result = $conn->exec(sprintf($queryFormat, $barcode));
  if ($result->ntuples != 1) {
    return undef;
  } else {
    return ($result->getvalue(0,0));
  }
}


sub
bob_db_get_userid_from_username
{
  my ($username) = @_;

  &bob_db_check_conn;
  my $queryFormat = q{
    select userid
    from users
    where username ~* '^%s$';
  };
  my $result = $conn->exec(sprintf($queryFormat, &esc_apos($username)));
  if ($result->ntuples != 1) {
    return $NOT_FOUND;
  } else {
    return ($result->getvalue(0,0));
  }
}


sub
bob_db_get_userid_from_userbarcode
{
  my ($barcode) = @_;

  &bob_db_check_conn;
  my $queryFormat = q{
    select userid
    from users
    where userbarcode = '%s';
  };
  my $result = $conn->exec(sprintf($queryFormat, $barcode));
  if ($result->ntuples != 1) {
    return $NOT_FOUND;
  } else {
    return ($result->getvalue(0,0));
  }
}


sub
bob_db_get_nickname_from_userid
{
  my ($userid) = @_;

  &bob_db_check_conn;
  my $queryFormat = q{
    select nickname
    from users
    where userid = %d;
  };
  my $result = $conn->exec(sprintf($queryFormat, $userid));
  if ($result->ntuples != 1) {
    return undef;
  } else {
    return ($result->getvalue(0,0));
  }
}


sub
bob_db_get_userbarcode_from_userid
{
  my ($userid) = @_;

  &bob_db_check_conn;
  my $queryFormat = q{
    select userbarcode
    from users
    where userid = %d;
  };
  my $result = $conn->exec(sprintf($queryFormat, $userid));
  if ($result->ntuples != 1) {
    return undef;
  } else {
    return ($result->getvalue(0,0));
  }
}


sub
bob_db_get_email_from_userid
{
  my ($userid) = @_;

  my $queryFormat = q{
    select email
    from users
    where userid = %d;
  };
  my $result = $conn->exec(sprintf($queryFormat, $userid));
  if ($result->ntuples != 1) {
    return undef;
  } else {
    return ($result->getvalue(0,0));
  }
}


sub
bob_db_add_user
{
  my ($username, $email) = @_;

  &bob_db_check_conn;
  my $insertqueryFormat = q{
    insert
    into users(userid, username, email)
    values(nextval('userid_seq'), '%s', '%s'); 
  };

  my $query = sprintf($insertqueryFormat, 
                      &esc_apos($username), 
                      &esc_apos($email));
  my $result = $conn->exec($query);
  if ($result->resultStatus != PGRES_COMMAND_OK) {
    my $mesg = "In bob_db_add_user: error inserting new user's record.\n" .
               "user: $username, $email";
    &report_fatal($mesg);
  }
}


sub
bob_db_update_user_barcode
{
  my ($userid, $barcode) = @_;

  &bob_db_check_conn;
  my $updatequeryFormat = q{
    update users
    set userbarcode = '%s'
    where userid = %d;
  };      

  my $result = $conn->exec(sprintf($updatequeryFormat, $barcode, $userid));
  if ($result->resultStatus != PGRES_COMMAND_OK) {
    my $mesg = "In bob_db_update_user_barcode: ";
    $mesg .= "error updating user's barcode.\n" .  
             "userid: $userid, barcode = $barcode";
    &report_fatal($mesg);
  }
}


sub
bob_db_update_nickname
{
  my ($userid, $name) = @_;

  &bob_db_check_conn;
  my $updatequeryFormat = q{
    update users
    set nickname = '%s'
    where userid = %d;
  };      

  my $result = $conn->exec(sprintf($updatequeryFormat, 
                                   &esc_apos($name), 
                                   $userid));
  if ($result->resultStatus != PGRES_COMMAND_OK) {
    my $mesg = "In bob_db_update_nickname: error updating user's nickname.\n" .
               "userid: $userid, nickname: $name";
    &report_fatal($mesg);
  }
}

#---------------------------------------------------------------------------
# balance table

sub
bob_db_get_balance
{
  my ($userid) = @_;

  &bob_db_check_conn;
  my $queryFormat = q{
    select balance
    from balances
    where userid = %d;
  };
  my $result = $conn->exec(sprintf($queryFormat,$userid));

  if ($result->ntuples != 1) {
    return $NOT_FOUND;
  } else {
    return ($result->getvalue(0,0));
  }
}


sub
bob_db_init_balance
{
  my ($userid) = @_;

  &bob_db_check_conn;
  my $insertqueryFormat = q{ 
    insert 
    into balances(userid, balance)
    values(%d, %.2f); 

    insert 
    into transactions(xacttime, userid, xactvalue, xacttype)
    values('now', %d, %.2f, 'INIT'); 
  };

  my $query = sprintf($insertqueryFormat, $userid, 0.0, $userid, 0.0);
  my $result = $conn->exec($query);
  if ($result->resultStatus != PGRES_COMMAND_OK) {
    my $mesg = "In bob_db_init_balance: error inserting record.\n" . 
               "userid: $userid";
    &report_fatal($mesg);
  }
}


sub
bob_db_update_balance
#
# Side effect: also updates the transactions table in addition to the entry
# in the balances table of 'userid'.  Note that 'amt' may be negative.
#
{
  my($userid, $amt, $type, $barcode, $privacy) = @_;

  $privacy = 0 if !defined($privacy);

  if (defined $barcode) {
    $barcode = "'" . &esc_apos($barcode) . "'";
  } else {
    $barcode = "NULL";
  }

  &bob_db_check_conn;
  my $updatequeryFormat = q{
    update balances
    set balance = balance + %.2f
    where userid = %d;

    insert
    into transactions(xacttime, userid, xactvalue, xacttype, barcode, source)
    values('now', %d, %.2f, '%s', %s, '%s'); 
  };

  my $query = sprintf($updatequeryFormat, 
                      $amt, 
                      $userid, 
                      $userid, 
                      $amt, 
                      &esc_apos(uc($type)),
                      $privacy ? "NULL" : $barcode,
                      $database_source);
  my $result = $conn->exec($query);
  if ($result->resultStatus != PGRES_COMMAND_OK) {
    my $mesg = "In bob_db_update_balance: error updating record.\n" .
               "userid: $userid, amt: $amt, type: $type";
    &report_fatal($mesg);
  }

  if ($barcode ne 'NULL') {
    $query = "insert into aggregate_purchases(date, barcode, quantity)
              values (now(), $barcode, 1);";
    $result = $conn->exec($query);
    if ($result->resultStatus != PGRES_COMMAND_OK) {
      my $mesg = "In bob_db_update_balance: error adding aggregate " .
                 "purchase record.\n" .
                 "type: $type, barcode: $barcode";
      &report_nonfatal($mesg);
    }
  }
}

#---------------------------------------------------------------------------
# msg table

sub
bob_db_insert_msg
{
  my ($userid, $msg) = @_;

  &bob_db_check_conn;
  my $insertqueryFormat = q{
    insert
    into messages(msgid, msgtime, userid, message)
    values( nextval('msgid_seq'), 'now', %s, '%s');
  };

  my $query = sprintf($insertqueryFormat, 
                      defined $userid ? $userid : "null", 
                      &esc_apos($msg));
  my $result = $conn->exec($query);
  if ($result->resultStatus != PGRES_COMMAND_OK) {
    my $mesg = "In bob_db_insert_msg: error inserting record.\n" .
               "userid: $userid, msg: $msg";
    &report_fatal($mesg);
  }
}

#---------------------------------------------------------------------------
# transactions table

sub
bob_db_log_transactions
{
  my ($userid, $logfile) = @_;

  &bob_db_check_conn;
  if ( !open(LOG_OUT, "> $logfile")) {
    my $mesg = "In bob_db_log_transaction: error writing to log file.\n" .
               "userid: $userid, logfile: $logfile";
    &report_fatal($mesg);
  }

  my $logqueryFormat = q{
    select date_trunc('second', xacttime), xactvalue, xacttype
    from transactions
    where userid = %d
    order by xacttime;
  };

  my $balance = 0.00;
  print LOG_OUT "Balance|         Time         |Amount|Description\n";
  my $result = $conn->exec(sprintf($logqueryFormat, $userid));
  for ($i = 0 ; $i < $result->ntuples ; $i++) {
    $time = $result->getvalue($i,0);
    $val = $result->getvalue($i,1);
    $type = $result->getvalue($i,2);
    $balance += $val;

    if ($i == 0) {
      $win_title .= " since $time";
    }

    print LOG_OUT sprintf("%7.2f|%22s|%6.2f|%s\n",
                          $balance, $time, $val, $type);
  }

  close(LOG_OUT);
}


#---------------------------------------------------------------------------
# pwd table

sub
bob_db_get_pwd
{
  my ($userid) = @_;

  &bob_db_check_conn;
  my $query = qq{
    select p
    from pwd
    where userid = $userid;
  };
  my $result = $conn->exec($query);

  if ($result->ntuples != 1) {
    return undef;
  } else {
    return $result->getvalue(0,0);
  }
}


sub
bob_db_remove_pwd
{
  my ($userid) = @_;

  &bob_db_check_conn;
  my $removequery = qq{
    delete
    from pwd
    where userid = $userid;
  };

  my $result = $conn->exec($removequery);
  if ($result->resultStatus != PGRES_COMMAND_OK) {
    my $mesg = "In bob_db_remove_pwd: error deleting record.\n" .
               "userid: $userid";
    &report_fatal($mesg);
  }
}


sub
bob_db_update_pwd
{
  my ($userid, $c_pwd) = @_;

  &bob_db_check_conn;
  my $updatequery = qq{
    update pwd
    set p = '$c_pwd'
    where userid = $userid;
  };

  my $result = $conn->exec($updatequery);
  if ($result->resultStatus != PGRES_COMMAND_OK) {
    my $mesg = "In bob_db_update_pwd: error updating record.\n" .
               "userid: $userid";
    &report_fatal($mesg);
  }
}


sub
bob_db_insert_pwd
{
  my ($userid, $c_pwd) = @_;

  &bob_db_check_conn;
  my $insertquery = qq{
    insert
    into pwd(userid, p)
    values($userid, '$c_pwd'); 
  };

  my $result = $conn->exec($insertquery);
  if ($result->resultStatus != PGRES_COMMAND_OK) {
    my $mesg = "In bob_db_insert_pwd: error inserting record.\n" .
               "userid: $userid";
    &report_fatal($mesg);
  }
}

#---------------------------------------------------------------------------
# products table

sub
bob_db_insert_product
{
  my ($barcode, $name, $phonetic_name, $price) = @_;
  &bob_db_check_conn;

  my $insertqueryFormat = q{
    insert 
    into products(barcode, name, phonetic_name, price)
    values('%s', '%s', '%s', %.2f);
  };      

  my $query = sprintf($insertqueryFormat, $barcode, &esc_apos($name), 
                      &esc_apos($phonetic_name), $price);
  my $result = $conn->exec($query);
  if ($result->resultStatus != PGRES_COMMAND_OK) {
    my $mesg = "In bob_db_insert_product: error inserting record.\n" .
               "$name, $barcode, $phonetic_name, $price";
    &report_fatal($mesg);
  }
}


sub
bob_db_get_productname_from_barcode
{
  my ($barcode) = @_;

  &bob_db_check_conn;
  my $selectqueryFormat = q{
    select name
    from products
    where barcode = '%s';
  };
  my $result = $conn->exec(sprintf($selectqueryFormat, $barcode));
  if ($result->ntuples != 1) {
    return undef;
  } else {
    return $result->getvalue(0,0);
  }
}


sub
bob_db_get_phonetic_name_from_barcode
{
  my ($barcode) = @_;

  &bob_db_check_conn;
  my $selectqueryFormat = q{
    select phonetic_name
    from products
    where barcode = '%s';
  };
  my $result = $conn->exec(sprintf($selectqueryFormat, $barcode));
  if ($result->ntuples != 1) {
    return undef;
  } else {
    return $result->getvalue(0,0);
  }
}


sub
bob_db_get_price_from_barcode
{
  my ($barcode) = @_;

  &bob_db_check_conn;
  my $selectqueryFormat = q{
    select price
    from products
    where barcode = '%s';
  };
  my $result = $conn->exec(sprintf($selectqueryFormat, $barcode));
  if ($result->ntuples != 1) {
    return $NOT_FOUND;
  } else {
    return $result->getvalue(0,0);
  }
}


sub
bob_db_delete_product
{
  my ($barcode) = @_;

  &bob_db_check_conn;
  my $deletequeryFormat = q{
    delete
    from products
    where barcode = '%s';
  };
  $result = $conn->exec(sprintf($deletequeryFormat, $barcode));
  if ($result->resultStatus != PGRES_COMMAND_OK) {
    my $mesg = "In bob_db_delete_product: error deleting record.\n" . "$barcode";
    &report_fatal($mesg);
  }
}

#---------------------------------------------------------------------------
# profiles table

sub
bob_db_get_profile_setting
{
  my ($userid, $property) = @_;
  &bob_db_check_conn;  
  my $queryFormat = q{
    select setting
    from profiles
    where userid = %d and property = '%s';
  };
  my $result = $conn->exec(sprintf($queryFormat, 
                                   $userid, 
                                   &esc_apos($property)));
  if ($result->ntuples != 1) {
    return $NOT_FOUND;
  } else {
    return $result->getvalue(0,0);
  }
}


sub
bob_db_insert_property
{
  my ($userid, $property) = @_;
  &bob_db_check_conn;
  my $insertqueryFormat = q{
    insert
    into profiles(userid, property, setting)
    values(%d, '%s', 0);
  };
  my $result = $conn->exec(sprintf($insertqueryFormat, 
                                   $userid, &esc_apos($property)));
  if ($result->resultStatus != PGRES_COMMAND_OK) {
    my $mesg = "In bob_db_insert_property: error inserting new property.\n" .
               "userid: $userid, property: $property";
    &report_fatal($mesg);
  }
}


sub
bob_db_update_profile_settings
{
  my ($userid, %newsettings) = @_;
  &bob_db_check_conn;

  while ( ($property, $setting) = each(%newsettings) ) {
    my $updatequeryFormat = q{
      update profiles
      set setting = %d
      where userid = %d and property = '%s'; 
    };
    my $query = sprintf($updatequeryFormat, 
                        $setting, 
                        $userid, 
                        &esc_apos($property));
    my $result = $conn->exec($query);
    if ($result->resultStatus != PGRES_COMMAND_OK) {
      my $mesg = "In bob_db_update_profile_setting: error updating profile.\n" . "userid: $userid, %newsettings";
      &report_fatal($mesg);
    }
  }
}

#---------------------------------------------------------------------------
# books table

sub
bob_db_insert_book
{
  my ($barcode, $isbn, $author, $title) = @_;
  &bob_db_check_conn;
  my $insertqueryFormat = q{
    insert
    into books(barcode, isbn, author, title)
    values('%s', '%s', '%s', '%s');
  };
  my $query = sprintf($insertqueryFormat, 
                      $barcode, 
                      $isbn, 
                      &esc_apos($author), 
                      &esc_apos($title));
  my $result = $conn->exec($query);
  if ($result->resultStatus != PGRES_COMMAND_OK) {
    my $mesg = "In bob_db_insert_book: error inserting new book.\n";
    &report_fatal($mesg);
  }
}


sub
bob_db_get_book_from_barcode
{
  my ($barcode) = @_;
  &bob_db_check_conn;

  my $selectqueryFormat = q{
    select author, title
    from books
    where barcode = '%s';
  };
  my $result = $conn->exec(sprintf($selectqueryFormat, $barcode));
  if ($result->ntuples < 1) {
    return undef;
  } else {
    return $result->getvalue(0,0) . "\t" . $result->getvalue(0,1);
  }
}

#---------------------------------------------------------------------------
# utilities 

sub
esc_apos
#
# escape any apostrophes using an extra apostrophe
#
{
  my ($str) = @_;
  $str =~ s/\'/\'\'/g;
  return $str;
}

#------------------------------------------------------------------------------ 
# Error reporting routines

sub report
{
  my ($subject, $mesg, @addresses) =  @_ ;

  my $MAIL = '/usr/bin/mail';
  my $fname = "/tmp/email$$";

  open(MESG, ">$fname") || die "can't open $fname: $!\n";
  print MESG &ctime(time), "\n";
  print MESG "$mesg";
  close(MESG);

  system("$MAIL -s \"$subject\" $ADMIN @addresses < $fname");
  unlink($fname);
}


sub report_fatal
{
  my ($message) = @_ ;
  my $subject = "BOB IS DOWN - a fatal error has occurred";

  print STDERR $message;
  &report($subject, $message);
  exit 1;
}


sub report_nonfatal
{
  my ($message) = @_ ;
  my $subject = "BOB ERROR - a non-fatal error has occurred";

  print STDERR $message;
  &report($subject, $message);
}


sub report_msg
{
  my ($userid, $message, @addresses) = @_ ;
  my ($subject) = "Message to Bob";
  &report($subject, $message, @addresses);
}

1;
