<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 3.2//EN">
<?php include('common.php') ?>

<HEAD>
	<TITLE>ChezBob Finance</TITLE>
</HEAD>

<BODY BGCOLOR=WHITE><TABLE BORDER=1 ALIGN=LEFT CELLSPACING=40><TR><TD>
	<?php db_connect() ?>
	
	<?php db_query('SELECT SUM(balance) FROM balances'); ?>
	<P>Total of balances is <?php $obj=db_nextObject(); echo $obj->sum; ?>.
	
	<?php db_close() ?>
</TD></TR></TABLE></BODY>
