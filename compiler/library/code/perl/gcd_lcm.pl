# НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). НОК = a / gcd * b.
use strict;
use warnings;

sub gcd {
    my ($a, $b) = @_;
    ($a, $b) = ($b, $a % $b) while $b;
    return $a;
}

sub lcm {
    my ($a, $b) = @_;
    return $a / gcd($a, $b) * $b;
}

print "GCD(48, 18) = ", gcd(48, 18), "\n";
print "LCM(48, 18) = ", lcm(48, 18), "\n";
