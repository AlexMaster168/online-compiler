# Ханойские башни: 2^n - 1 ходов. Возвращаем число ходов.
use strict;
use warnings;

sub hanoi {
    my ($n, $source, $spare, $target) = @_;
    return 0 if $n == 0;
    my $before = hanoi($n - 1, $source, $target, $spare);
    print "Move disk $n from $source to $target\n";
    return $before + 1 + hanoi($n - 1, $spare, $source, $target);
}

print "Total moves: ", hanoi(3, "A", "B", "C"), "\n";
