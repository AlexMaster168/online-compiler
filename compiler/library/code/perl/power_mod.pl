# Быстрое возведение в степень: O(log n). Произведение < 2^63 — 64-битных целых хватает.
use strict;
use warnings;
use integer;  # целочисленная арифметика без ухода в float

use constant MOD => 1_000_000_007;

sub power_mod {
    my ($base, $exp, $mod) = @_;
    my $result = 1;
    $base %= $mod;
    while ($exp > 0) {
        $result = $result * $base % $mod if $exp & 1;
        $base = $base * $base % $mod;
        $exp >>= 1;
    }
    return $result;
}

print "2^30 mod ", MOD, " = ", power_mod(2, 30, MOD), "\n";
print "3^200 mod ", MOD, " = ", power_mod(3, 200, MOD), "\n";
