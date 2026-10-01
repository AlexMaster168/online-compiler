# Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован.
use strict;
use warnings;

sub bubble_sort {
    my @a = @_;
    for my $i (0 .. $#a - 1) {
        my $swapped = 0;
        for my $j (0 .. $#a - 1 - $i) {
            if ($a[$j] > $a[$j + 1]) {
                @a[$j, $j + 1] = @a[$j + 1, $j];
                $swapped = 1;
            }
        }
        last unless $swapped;
    }
    return @a;
}

print "Sorted: ", join(" ", bubble_sort(5, 2, 9, 1, 5, 6)), "\n";
