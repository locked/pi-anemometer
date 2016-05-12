<?php

require_once "pdo.php";

$types = array(
	"temp",
	"pressure",
	"wind_speed",
);

$summarize = 600;

$start_ts = time() - 86400;
$end_ts = time();

if( isset($_GET["from"]) ) {
	if( preg_match("/\-(\d+)h[our]*/", $_GET["from"], $matches) ) {
		$start_ts = strtotime("-".$matches[1]."hour");
	} elseif( preg_match("/\-(\d+)d[ay]*/", $_GET["from"], $matches) ) {
		$start_ts = strtotime("-".$matches[1]."hour");
	} elseif( preg_match("/\d+/", $_GET["from"]) ) {
		$start_ts = $_GET["from"];
	}
}
if( isset($_GET["until"]) ) {
	if( preg_match("/\-(\d+)h[our]*/", $_GET["until"], $matches) ) {
		$end_ts = strtotime("-".$matches[1]."hour");
	} elseif( preg_match("/\-(\d+)d[ay]*/", $_GET["until"], $matches) ) {
		$end_ts = strtotime("-".$matches[1]."hour");
	} elseif( preg_match("/\d+/", $_GET["until"]) ) {
		$end_ts = $_GET["until"];
	}
}

$res = array();
foreach( $types as $type ) {
	$q = "SELECT round(ts/".$summarize.") * ".$summarize." as rts, sensor, avg(value) as value FROM raw WHERE ts > :start_ts AND ts < :end_ts AND type = :type GROUP BY rts, sensor ORDER BY rts ASC";
	$stmt = $db->prepare($q);
	$args = array(
		"type" => $type,
		"start_ts" => $start_ts,
		"end_ts" => $end_ts,
	);
	//echo "q:$q args:".json_encode($args)."]<br>";
	$stmt->execute($args);
	$rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
	$tmpres = array();
	foreach( $rows as $row ) {
		$ts = date("Y-m-d H:i:s", $row["rts"]);
		if( !isset($res[$ts]) ) {
			$res[$ts] = array();
		}
		$tmpres[$ts]["value_".$row["sensor"]] = $row["value"];
	}
	$res[$type] = $tmpres;
}

?>
<html>
  <head>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript">
    google.charts.load('current', {'packages':['corechart']});

    var weather_data = {
      "temp": [
        ['Date', 'MCP', 'BMP', 'RPI'],
	<?php $i = 0; foreach( $res["temp"] as $date => $r ): ?>
          ['<?php echo $date ?>', <?php echo $r["value_mcp"] ?>, <?php echo $r["value_bmp"] ?>, <?php echo floatval($r["value_rpi"]); ?>]<?php echo ++$i < count($res["temp"]) ? "," : ""; ?>
	<?php endforeach; ?>
      ],
      "pressure": [
        ['Date', 'Pressure'],
	<?php $i = 0; foreach( $res["pressure"] as $date => $r ): ?>
          ['<?php echo $date ?>', <?php echo $r["value_bmp"] ?>]<?php echo ++$i < count($res["pressure"]) ? "," : ""; ?>
	<?php endforeach; ?>
      ],
      "wind_speed": [
        ['Date', 'Wind Speed'],
	<?php $i = 0; foreach( $res["wind_speed"] as $date => $r ): ?>
          ['<?php echo $date ?>', <?php echo $r["value_external"] ?>]<?php echo ++$i < count($res["wind_speed"]) ? "," : ""; ?>
	<?php endforeach; ?>
      ]
    };
    //google.charts.setOnLoadCallback(drawChart);

      function drawChart(chart_type) {
        var data = google.visualization.arrayToDataTable(weather_data[chart_type]);

        var options = {
          title: chart_type,
          curveType: 'function',
          legend: { position: 'bottom' }
        };

        var chart = new google.visualization.LineChart(document.getElementById(chart_type+'_chart'));

        chart.draw(data, options);
      }
    function go() {
      drawChart("temp");
      drawChart("pressure");
      drawChart("wind_speed");
    }
    </script>
  </head>
  <body onLoad="go()">
    <h2><?php echo date("Y-m-d H:i", $start_ts)." to ".date("Y-m-d H:i", $end_ts); ?></h2>
    <div id="temp_chart" style="width: 1100px; height: 600px"></div>
    <div id="pressure_chart" style="width: 1100px; height: 600px"></div>
    <div id="wind_speed_chart" style="width: 1100px; height: 600px"></div>
  </body>
</html>
