<?php

require_once "pdo.php";

$raw_input = file_get_contents('php://input');
$input = json_decode($raw_input, true);

$items = $input["items"];
#error_log(json_encode($items));

foreach( $items as $item ) {
	unset($item["unit"]);
	$q = "INSERT INTO raw (type, sensor, ts, value) VALUES (:type, :sensor, :ts, :value)";
	error_log("q:$q item:".json_encode($item)."]");
	$stmt = $db->prepare($q);
	$stmt->execute($item);
}

$res = array("status" => 0);

echo json_encode($res);
