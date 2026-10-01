# Поиск в ширину: массив как очередь (shift/push), O(V + E).
use strict;
use warnings;

my @graph = ([1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]);
my @dist = (-1) x @graph;
my (@order, @queue);
$dist[0] = 0;
push @queue, 0;
while (@queue) {
    my $v = shift @queue;
    push @order, $v;
    for my $u (@{ $graph[$v] }) {
        next unless $dist[$u] == -1;
        $dist[$u] = $dist[$v] + 1;
        push @queue, $u;
    }
}
print "BFS order: @order\n";
print "Distances: @dist\n";
