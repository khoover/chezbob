<?php
/**
 * ----------------------------------------------
 * Advanced Poll 2.0.2 (PHP)
 * Copyright (c)2001 Chi Kien Uong
 * URL: http://www.proxy2.de
 * ----------------------------------------------
 */
 
$include_path = dirname(__FILE__);
$base_path = dirname($include_path);

require "./common.inc.php";

function reset_log($poll_id) {
    global $base_path;
    if (file_exists("$base_path/polldata/$poll_id.log")) {
        $fp = fopen("$base_path/polldata/$poll_id.log","w");
        fclose($fp);
    }
}

if (!isset($action)) {
    $action='';
}
if ($action=="reset" and isset($poll_id)) {
    reset_log($poll_id);
}

$time_offset = $pollvars['time_offset']*3600;
$line = file("$base_path/polldata/$poll_id");
list($question,$timestamp,$exp_time,$expire,$logging,$status,$comments) = split("\\|",$line[0]);
$question = htmlspecialchars($question);
$use_opt = sizeof($line);
$poll_sum_total = 0;
for ($i=1; $i<$use_opt; $i++) {
    list($name,$vote,$gif_color) = split("\\|",$line[$i]);
    $option_text[] = $name;
    $votes[] = $vote;
    $poll_sum_total += $vote;
}
list($wday,$mday,$month,$year,$hour,$minutes) = split("( )",date("w j n Y H i",$timestamp+$time_offset));
$newdate = "$weekday[$wday], $mday ".$months[$month-1]." $year $hour:$minutes";

$CLASS["template"]->set_templatefiles(array(
    "admin_stats" => "admin_stats.html"
));
$poll_stats = "<table width=\"100%\" border=\"0\" cellspacing=\"0\" cellpadding=\"2\">";
$hours = (int) ((time()-$timestamp+$time_offset)/3600);
$days = (int) ($hours/24);
$remain = $hours%24;
$question = htmlspecialchars($question);

for ($i=0,$k=1; $i<$use_opt-1; $i++,$k++) {
    $percent = ($poll_sum_total == 0) ? "0%" : sprintf("%.2f",($votes[$i]*100/$poll_sum_total))."%";
    $perday = ($days>0) ? sprintf("%.1f",($votes[$i]/$days)) : $votes[$i];
    $poll_stats .= "              <tr>
                <td colspan=\"4\" class=\"td2\"><b>$lang[NewOption] $k: $option_text[$i]</b></td>
              </tr>
              <tr>
                <td colspan=\"2\" class=\"td2\">- $lang[SetVotes]: <font color=\"#CC0000\">$votes[$i]</font> ($percent)</td>
                <td colspan=\"2\" class=\"td2\" width=\"80%\">- <font color=\"#0000FF\">$perday</font> $lang[StatDay]</td>
              </tr>\n";
}
$poll_stats .= "            </table>\n";
if ($logging == 1 && file_exists("$base_path/polldata/$poll_id.log")) {
    $log_array = file("$base_path/polldata/$poll_id.log");
    if (sizeof($log_array)>0) {
        $poll_stats .= "            <table width=\"100%\" border=\"0\" cellspacing=\"1\" cellpadding=\"1\" bgcolor=\"#000000\">
            <tr bgcolor=\"#000084\">
              <td width=\"15%\" height=\"22\" class=\"td2\"><font color=\"#FFFFFF\"><b>$lang[IndexDate]</b></font></td>
              <td width=\"13%\" height=\"22\" class=\"td2\"><font color=\"#FFFFFF\"><b>IP</b></font></td>
              <td width=\"32%\" height=\"22\" class=\"td2\"><font color=\"#FFFFFF\"><b>Host</b></font></td>
              <td width=\"40%\" height=\"22\" class=\"td2\"><font color=\"#FFFFFF\"><b>Browser</b></font></td>
            </tr>\n";
        for ($s=sizeof($log_array)-1; $s>=0; $s--) {
        list($time,$ip,$hostname,$browser) = split("\\|",$log_array[$s]);
        $poll_stats .= "              <tr bgcolor=\"#C6C3C6\">
              <td width=\"15%\" class=\"td2\">$time</td>
              <td width=\"13%\" class=\"td2\">$ip</td>
              <td width=\"32%\" class=\"td2\">$hostname</td>
              <td width=\"40%\" class=\"td2\">$browser</td>
            </tr>\n";
        }
        $poll_stats .= "          </table>\n";
    }
}

$admin_stats = $CLASS["template"]->pre_parse("admin_stats");
no_cache_header();
eval("echo \"$admin_stats\";");

?>