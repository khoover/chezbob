#
# Routine to report error to system admin.
# Exit with status 1.
#

#use Time::localtime;
require "ctime.pl";

$ADMIN = 'chpham@danger-132.ucsd.edu';

sub
report_fatal
{
}

sub
report_msg
{
}

#------------------------------------------------------------------------------ 
# report()
#
# Email system admin.
#------------------------------------------------------------------------------ 
sub report 
{
 my ($mesg) =  @_ ;

 my $MAIL = '/bin/mail';
 my $fname = "/tmp/email$$";
 my $subject = 'Chez Bob Database problem';

 open(MESG, ">$fname") || die "can't open $fname: $!\n";
 print MESG &ctime(time), "\n\n";
 print MESG "$mesg";
 close(MESG);

 system("$MAIL -s \"$subject\" $ADMIN < $fname");
 unlink($fname);

 exit 1;
}

1;
