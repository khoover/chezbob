<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 3.2//EN">
<?php include('common.php') ?>

<HEAD>
	<TITLE>ChezBob Finance</TITLE>
</HEAD>

<BODY BGCOLOR=WHITE><TABLE BORDER=1 ALIGN=LEFT CELLSPACING=40>
	<TR><TD WIDTH=400 ALIGN=LEFT>
	<?php db_connect() ?>
	
	<?php db_query('SELECT SUM(balance) FROM balances');
		  $obj=db_nextObject(); ?>
	<P>Total of balances is $<?php  echo $obj->sum; ?>.
	
	<?php db_query('SELECT SUM(balance) FROM balances WHERE balance > 0');
		  $obj=db_nextObject(); ?>
	<P>Total of positive balances is $<?php  echo $obj->sum; ?>.
	
	<?php db_query('SELECT SUM(balance) FROM balances WHERE balance < 0');
		  $obj=db_nextObject(); ?>
	<P>Total of negative balances is $<?php  echo $obj->sum; ?>.
	
	<?php db_close() ?>
	</TD></TR>
</TABLE></BODY>
