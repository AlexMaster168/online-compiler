# Факториал рекурсией. 20! ещё влезает в 64-битное целое Perl.
use strict;
use warnings;

sub factorial {
    my $n = shift;
    return $n <= 1 ? 1 : $n * factorial($n - 1);
}

print "10! = ", factorial(10), "\n";
print "20! = ", factorial(20), "\n";
