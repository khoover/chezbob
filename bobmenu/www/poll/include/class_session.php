<?php
/**
 * ----------------------------------------------
 * Advanced Poll 2.0.2 (PHP)
 * Copyright (c)2001 Chi Kien Uong
 * URL: http://www.proxy2.de
 * ----------------------------------------------
 */

class poll_session {

    var $expire = 7200;
    var $include_path;

    function poll_session($path='') {
        if (empty($path)) {
            $this->include_path = dirname(__FILE__);
        } else {
            $this->include_path = $path;
        }
    }

    function set_session_time($expire_time='') {
        if ($expire_time>0) {
            $this->expire = $expire_time;
        }
    }

    function is_valid_session($session,$uid) {
        include "$this->include_path/session.php";
        if ($session == $auth['session'] and $uid = $auth['uid']) {            
            return ($this->expire + $auth['expire'] > time()) ? $auth['session'] : false;
        } else {
            return false;
        }
    }

    function generate_new_session_id($user_id) {
        srand((double)microtime()*1000000);
        $session = md5 (uniqid (rand()));
        $unix_time = time();
        $config="<?php\n";
        $config.="\$auth['session']=\"$session\";\n";
        $config.="\$auth['uid']=\"$user_id\";\n";
        $config.="\$auth['expire']=\"$unix_time\";\n";
        $config.="?>";
        $fp = fopen("$this->include_path/session.php","w");
        flock($fp, 2);
        fwrite($fp, $config);
        flock($fp, 3);
        fclose($fp);
        return $session;
    }

    function check_pass($username,$password) {
        global $pollvars;
        $password = md5($password);
        return ($pollvars['poll_username']==$username and $pollvars['poll_password']==$password) ? 1 : false;
    }

    function check_session_id() {
        global $username, $password, $session, $uid;
        if (isset($session) && isset($uid)) {
            return ($this->is_valid_session($session,$uid)) ? array("session" => "$session", "uid" => "$uid") : false;
        } elseif (isset($username) && isset($password)) {
            if (get_magic_quotes_gpc()) {
                $username = stripslashes($username);
                $password = stripslashes($password);
            }
            $ID = $this->check_pass($username,$password);
            if ($ID) {
                $session = $this->generate_new_session_id($ID);
                return array("session" => "$session", "uid" => "$ID");
            } else {
                return false;
            }
        } else {
            return false;
        }

    }

}

?>