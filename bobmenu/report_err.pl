#! /usr/bin/perl -w

#------------------------------------------------------------------------------ 
# ctime()
#
#	Get current date and time.
#------------------------------------------------------------------------------ 
sub ctime
{
	my $fname = 'bob_err_time.txt';
	my $date_arg = '%m %d %y %H %M %S';
	system("/bin/date +\"$date_arg\" > $fname");

	unless (open(TIME, "$fname"))
	{
    	print "ERR: failed to open $fname";
		exit 1;
	} 
	else 
	{
		chomp($date = <TIME>);
	}
	close(TIME);
	unlink($fname);
	return $date;
}

#------------------------------------------------------------------------------ 
# report()
#
#	Report errors to system admin.
#------------------------------------------------------------------------------ 
sub report 
{
	my ($mesg) =  @_ ;
	my ($mon, $day, $year, $hour, $min, $sec) = split(/ /, &ctime());
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
		print MESG "On $day/$mon/$year \@ $hour:$min:$sec\n\n";
		print MESG "$mesg";
	}
	close(MESG);

	system("$MAIL -s \"$subject\" $ADMIN < $fname");
	unlink($fname)

	exit 1;
}
1;

#$mesg = "Connection to the Chez Bob database lost";
#&report("$mesg");
