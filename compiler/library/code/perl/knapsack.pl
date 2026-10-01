# Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз.
use strict;
use warnings;

my @weights = (1, 3, 4, 5);
my @values = (1, 4, 5, 7);
my $capacity = 7;
my @dp = (0) x ($capacity + 1);
for my $i (0 .. $#weights) {
    for (my $c = $capacity; $c >= $weights[$i]; $c--) {
        my $take = $dp[$c - $weights[$i]] + $values[$i];
        $dp[$c] = $take if $take > $dp[$c];
    }
}
print "Knapsack max value: $dp[$capacity]\n";
