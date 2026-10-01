# Числа Фибоначчи итеративно, O(n). Perl на 64-битной сборке хранит F(50) в целом без потерь.
use strict;
use warnings;

sub fib {
    my $n = shift;
    my ($a, $b) = (0, 1);
    ($a, $b) = ($b, $a + $b) for 1 .. $n;
    return $a;
}

print "Fibonacci: ", join(" ", map { fib($_) } 0 .. 14), "\n";
print "F(50) = ", fib(50), "\n";
