# Быстрая сортировка (разбиение Ломуто): массив передаём ссылкой, сортируем на месте.
use strict;
use warnings;

sub partition {
    my ($a, $lo, $hi) = @_;
    my $pivot = $a->[$hi];
    my $i = $lo;
    for my $j ($lo .. $hi - 1) {
        if ($a->[$j] < $pivot) {
            @$a[$i, $j] = @$a[$j, $i];
            $i++;
        }
    }
    @$a[$i, $hi] = @$a[$hi, $i];
    return $i;
}

sub quick_sort {
    my ($a, $lo, $hi) = @_;
    return if $lo >= $hi;
    my $p = partition($a, $lo, $hi);
    quick_sort($a, $lo, $p - 1);
    quick_sort($a, $p + 1, $hi);
}

my @data = (10, 7, 8, 9, 1, 5, 3);
quick_sort(\@data, 0, $#data);
print "Sorted: @data\n";
