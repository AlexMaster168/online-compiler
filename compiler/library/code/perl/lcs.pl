# Наибольшая общая подпоследовательность: dp[i][j] — длина LCS для префиксов. O(n * m).
use strict;
use warnings;
use List::Util qw(max);

sub lcs {
    my @a = split //, shift;
    my @b = split //, shift;
    my @dp = map { [(0) x (@b + 1)] } 0 .. @a;
    for my $i (1 .. @a) {
        for my $j (1 .. @b) {
            $dp[$i][$j] = $a[$i - 1] eq $b[$j - 1]
                ? $dp[$i - 1][$j - 1] + 1
                : max($dp[$i - 1][$j], $dp[$i][$j - 1]);
        }
    }
    return $dp[@a][@b];
}

print "LCS(ABCBDAB, BDCABA) = ", lcs("ABCBDAB", "BDCABA"), "\n";
