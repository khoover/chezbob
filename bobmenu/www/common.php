<?
include('io.php');
// MySQL user preferences
define('SQL_DB','bob');

$db_conn = 0;
$db_query = 0;

function db_error(){ }

function db_connect(){
	global $db_conn;
    // connect to our database
	$db_conn = pg_connect("user=".SQL_DB);
	if ($db_conn == 0) {
		echo "Database connect failed\n";
		db_error();
	}
}

function db_query($query){
	global $db_conn;
	if ($db_conn == 0) {
		db_error();
		return NULL;
	}
	global $db_query;
	$db_query = pg_exec($db_conn, $query);
}

function db_nextobject(){
	static $row = 0;
	global $db_query;
	if ($db_query == 0) {
		db_error();
		return 0;
	}
	$obj = @pg_fetch_object($db_query, $row);
	$row++;
	return $obj;
}

function db_freeQuery($query_handle){
	if ($query_handle != 0)	{
		pg_freeResult($query_handle);
	}
}

function db_closeConn($db_handle){
	if ($db_handle != 0) {
		pg_close($db_handle);
	}
}

function db_close(){
	global $db_conn;
	global $db_query;
	db_freeQuery($db_query);
	db_closeConn($db_conn);
}

function makeHeader($pageTitle){
$ret= "<html><head><title>".$pageTitle."</title>\n";
$ret=$ret."</head>\n<body bgcolor='white'>\n"; 
$in = easyRead('header');
$ret=$ret.$in;
return $ret;
}

function makeHeaderWithStyle($pageTitle){
$ret= "<html><head><title>".$pageTitle."</title>\n";
$in= easyRead('style');
$ret=$ret.$in;
$ret=$ret."</head>\n<body bgcolor='white'>\n"; 
$in = easyRead('header');
$ret=$ret.$in;
return $ret;
}

function makeFooter(){
  $in= easyRead('footer');
  $in = $in."</body></html>";
  return $in;
}

?>

