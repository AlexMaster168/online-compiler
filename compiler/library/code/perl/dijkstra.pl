# Дейкстра за O(V^2): каждый раз берём ближайшую непосещённую вершину.
use strict;
use warnings;

my @edges = ([[1, 4], [2, 1]], [[3, 1]], [[1, 2], [3, 5]], [[4, 3]], []);
my $INF = 9**9**9;
my @dist = ($INF) x @edges;
my @done = (0) x @edges;
$dist[0] = 0;
for (1 .. @edges) {
    my ($v) = sort { $dist[$a] <=> $dist[$b] } grep { !$done[$_] } 0 .. $#edges;
    last if $dist[$v] == $INF;
    $done[$v] = 1;
    for my $edge (@{ $edges[$v] }) {
        my ($u, $w) = @$edge;
        $dist[$u] = $dist[$v] + $w if $dist[$v] + $w < $dist[$u];
    }
}
print "Dijkstra from 0: @dist\n";
