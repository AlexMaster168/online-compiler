<?php
// Поиск в глубину рекурсией: O(V + E).
const GRAPH = [[1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]];

function dfs(int $v, array &$visited, array &$order): void
{
    $visited[$v] = true;
    $order[] = $v;
    foreach (GRAPH[$v] as $u) {
        if (empty($visited[$u])) {
            dfs($u, $visited, $order);
        }
    }
}

$visited = [];
$order = [];
dfs(0, $visited, $order);
echo "DFS order: " . implode(" ", $order) . "\n";
