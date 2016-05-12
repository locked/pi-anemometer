<?php

$dbhost = "127.0.0.1";
$dbname = "weather";
$dbuser = "weather";
$dbpswd = "";
$db = new PDO("mysql:host=".$dbhost.";dbname=".$dbname, $dbuser, $dbpswd);

