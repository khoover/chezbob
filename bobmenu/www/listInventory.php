<?php
include('common.php');

function getInventoryFromSQL(){
$out = makeHeader("Chez Bob Inventory");

db_connect();
db_query('SELECT * from products ORDER by name;');
$colora = ' bgcolor="#CCCCFF" bordercolor="#CCCCFF"';
$colorb = ' bgcolor="#CCCCCC" bordercolor="#CCCCCC"';
$rowcolor = ' ';
$rowCount = 0;

$out=$out."<table width='75%' border=1 cellspacing=0 cellpadding=0>\n"; 
$out=$out.'<tr'.$rowcolor.'><td><b>Product Name'."</b></td>\n";
$out=$out.'<td><b>Number in Stock'."</b></td></tr>\n";

//while (($obj = db_nextObject()) && ($obj != NULL)) {
while ($obj = db_nextObject()) {
    if ($rowCount++ % 2 == 0)
      $rowcolor = $colora;
    else
      $rowcolor = $colorb; 

    $out=$out.'<tr'.$rowcolor.'><td>'.$obj->name."</td>\n";
    $out=$out.'<td>'.$obj->stock."</td></tr>\n";
}
db_close();
$moreout = makeFooter();
$out=$out.'</table>';
return $out;
}

$out = getInventoryFromSQL();
echo $out;

?>
