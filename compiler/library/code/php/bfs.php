<?php
// Поиск в ширину: SplQueue, O(V + E).
$graph = [[1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]];
$dist = array_fill(0, count($graph), -1);
$order = [];
$queue = new SplQueue();
$dist[0] = 0;
$queue->enqueue(0);
while (!$queue->isEmpty()) {
    $v = $queue->dequeue();
    $order[] = $v;
    foreach ($graph[$v] as $u) {
        if ($dist[$u] === -1) {
            $dist[$u] = $dist[$v] + 1;
            $queue->enqueue($u);
        }
    }
}
echo "BFS order: " . implode(" ", $order) . "\n";
echo "Distances: " . implode(" ", $dist) . "\n";
