<?php

require_once "pdo.php";

$types = array(
	"temp",
	"wind_speed",
	"wind_direction",
	"pressure",
	"altitude",
	"sealevel_pressure",
	"pluvio",
);

$all = array();
foreach( $types as $type ) {
	$q = "SELECT * FROM raw WHERE type = :type ORDER BY ts DESC LIMIT 100";
	$stmt = $db->prepare($q);
	$args = array(
		"type" => $type,
	);
	//echo "q:$q args:".json_encode($args)."]<br>";
	$stmt->execute($args);
	$all[$type] = $stmt->fetchAll(PDO::FETCH_ASSOC);
}

foreach( $all as $type => $res ): ?>
	<h2><?php echo $type; ?></h2>
	<table width="100%">
	<?php foreach( $res as $r ): ?>
		<tr>
		<td><?php echo date("c", $r["ts"]) ?></td>
		<td><?php echo $r["value"] ?></td>
		<td><?php echo $r["sensor"] ?></td>
		</tr>
	<?php endforeach; ?>
	</table>
<?php endforeach; ?>
