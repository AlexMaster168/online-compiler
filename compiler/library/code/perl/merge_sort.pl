# Сортировка слиянием: всегда O(n log n), стабильная.
use strict;
use warnings;

sub merge_sort {
    my @a = @_;
    return @a if @a <= 1;
    my $mid = int(@a / 2);
    my @left = merge_sort(@a[0 .. $mid - 1]);
    my @right = merge_sort(@a[$mid .. $#a]);
    my @merged;
    while (@left && @right) {
        push @merged, ($left[0] <= $right[0] ? shift @left : shift @right);
    }
    return (@merged, @left, @right);
}

my @sorted = merge_sort(38, 27, 43, 3, 9, 82, 10);
print "Sorted: @sorted\n";
