<?php
// Дейкстра с SplPriorityQueue (она максимальная — кладём приоритет со знаком минус).
$graph = [[[1, 4], [2, 1]], [[3, 1]], [[1, 2], [3, 5]], [[4, 3]], []];
$dist = array_fill(0, count($graph), PHP_INT_MAX);
$dist[0] = 0;
$pq = new SplPriorityQueue();
$pq->setExtractFlags(SplPriorityQueue::EXTR_BOTH);
$pq->insert(0, 0);
while (!$pq->isEmpty()) {
    ['data' => $v, 'priority' => $negDist] = $pq->extract();
    $d = -$negDist;
    if ($d > $dist[$v]) {
        continue;  // устаревшая запись
    }
    foreach ($graph[$v] as [$u, $w]) {
        if ($d + $w < $dist[$u]) {
            $dist[$u] = $d + $w;
            $pq->insert($u, -$dist[$u]);
        }
    }
}
echo "Dijkstra from 0: " . implode(" ", $dist) . "\n";
