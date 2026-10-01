# Бинарный поиск: O(log n), массив обязан быть отсортирован.
use strict;
use warnings;

sub binary_search {
    my ($a, $target) = @_;
    my ($lo, $hi) = (0, $#$a);
    while ($lo <= $hi) {
        my $mid = int(($lo + $hi) / 2);
        return $mid if $a->[$mid] == $target;
        if ($a->[$mid] < $target) { $lo = $mid + 1 } else { $hi = $mid - 1 }
    }
    return -1;
}

my @arr = (1, 3, 5, 7, 9, 11, 13, 15, 17, 19);
for my $target (7, 4) {
    my $i = binary_search(\@arr, $target);
    print $i >= 0 ? "Found $target at index $i\n" : "$target not found\n";
}
