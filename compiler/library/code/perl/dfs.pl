# Поиск в глубину рекурсией: O(V + E).
use strict;
use warnings;

my @graph = ([1, 2], [0, 3], [0, 4], [1, 5], [2, 5], [3, 4]);
my (%visited, @order);

sub dfs {
    my $v = shift;
    $visited{$v} = 1;
    push @order, $v;
    # Проверяем visited в момент захода, а не заранее через grep: пока обходим одного соседа,
    # рекурсия может посетить другого
    for my $u (@{ $graph[$v] }) {
        dfs($u) unless $visited{$u};
    }
}

dfs(0);
print "DFS order: @order\n";
