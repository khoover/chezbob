<?php

// Modified by Michael Vrable <mvrable@cs.ucsd.edu> February 3, 2006.
//
// Don't display user e-mail addresses--do we really want to be publishing
// these for all to see on the web?

include('common.php');

function getMoneyString($val) {
   if (($val*100)%100 == 0) {
      return $val . ".00";
   } else if (($val*100)%10 == 0) {
      return $val . "0";
   } else {
      return $val;
   }
}

function getLosersFromSQL() {
	$out = makeHeader("Chez Bob Wall of Shame", "header.shame");

	db_connect();
	db_query('SELECT username, email, nickname, balance FROM users, balances WHERE balance <= -5 AND users.userid=balances.userid ORDER BY balance;');
	$colora = ' bgcolor="#CCCCFF" bordercolor="#CCCCFF"';
	$colorb = ' bgcolor="#CCCCCC" bordercolor="#CCCCCC"';
	$rowcolor = ' ';
	$rowCount = 0;

	$out=$out."<table width='75%' border=1 cellspacing=0 cellpadding=0>\n"; 
	$out=$out.'<tr'.$rowcolor.'><td><b>User Name'."</b></td>\n";
	//$out=$out.'<td><b>Email'."</b></td>\n";
	$out=$out.'<td><b>Owed Bob'."</b></td></tr>\n";

	while ($obj = db_nextObject()) {
	    if ($rowCount++ % 2 == 0)
	      $rowcolor = $colora;
	    else
	      $rowcolor = $colorb; 

	    $out=$out.'<tr'.$rowcolor.'><td>'.$obj->username;
	    if ($obj->nickname!=NULL) {
	       $out=$out." (aka ".$obj->nickname.")</td>\n";
	    } else {
	       $out=$out."</td>\n";
	    }
	    //$out=$out.'<td>'.$obj->email."</td>\n";
	    $out=$out.'<td>$'.getMoneyString(-1*$obj->balance)."</td></tr>\n";
	}
	db_close();
	$moreout = makeFooter();
	$out=$out.'</table>';
	return $out;
}

$out = getLosersFromSQL();
echo $out;

?>
