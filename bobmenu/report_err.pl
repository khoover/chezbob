#
#	Routine to report error to system admin.
#	Exit with status 1.
#

use Time::localtime;

#------------------------------------------------------------------------------ 
# report()
#
#	Report errors to system admin.
#------------------------------------------------------------------------------ 
sub report 
{
	my ($mesg) =  @_ ;

	my $lt = localtime();
	my ($hour, $min, $sec) = ($lt->hour, $lt->min, $lt->sec);
	my $fname = "mesg.${hour}${min}${sec}.tmp";

	my $MAIL = '/bin/mail';
	my $ADMIN = 'chpham@danger-132.ucsd.edu';
	my $subject = 'Chez Bob Database problem';

	unless (open(MESG, ">$fname"))
	{
    	print "ERR: failed to create $fname";
		exit 1;
	} 
	else 
	{
		print MESG &ctime(), "\n\n";
		print MESG "$mesg";
	}
	close(MESG);

	system("$MAIL -s \"$subject\" $ADMIN < $fname");
	unlink($fname);

	exit 1;
}
1;
