<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 3.2//EN">
<?php include('common.php') ?>

<HEAD>
	<TITLE>ChezBob Finance</TITLE>
</HEAD>

<BODY BGCOLOR=WHITE><TABLE BORDER=0 ALIGN=CENTER CELLSPACING=40>
	<TR><TD WIDTH=400 ALIGN=LEFT>
	<?php
		$conn = pg_connect("user=bob");
		if ($conn == 0) {
			echo "<FONT SIZE=+1><STRONG>Failed to connect to database.</STRONG></FONT>";
		} else {
			// Get sum of positive balances.
			$query = "SELECT SUM(balance) FROM balances WHERE balance > 0";
			$result = pg_exec($conn, $query);
			$row = pg_fetch_object($result, 0);
			$positiveBalance = $row->sum;
			pg_freeResult($result);
			
			// Get sum of negative balances.
			$query = "SELECT SUM(-balance) FROM balances WHERE balance < 0";
			$result = pg_exec($conn, $query);
			$row = pg_fetch_object($result, 0);
			$negativeBalance = $row->sum;
			pg_freeResult($result);
			
			// Compute total balance and finish.
			$totalBalance = $positiveBalance - $negativeBalance;
			pg_close($conn);
	?>
	<H1>ChezBob Finance Summary</H1>
	<P>Total of balances is <?php echo $positiveBalance; ?> - <?php echo $negativeBalance; ?> = <?php echo $totalBalance; ?>.
	
	<?php } // $conn != 0 ?>
	</TD></TR>
</TABLE></BODY>
