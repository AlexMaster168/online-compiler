# Решето Эратосфена: O(n log log n).
use strict;
use warnings;

my $n = 50;
my @composite;
my @primes;
for my $p (2 .. $n) {
    next if $composite[$p];
    push @primes, $p;
    for (my $k = $p * $p; $k <= $n; $k += $p) { $composite[$k] = 1 }
}
print "Primes up to $n: @primes\n";
