// Сортировка пузырьком: O(n^2). Срез []i32 — указатель плюс длина, меняем массив на месте.
const std = @import("std");

fn bubbleSort(a: []i32) void {
    var i: usize = 0;
    while (i + 1 < a.len) : (i += 1) {
        var swapped = false;
        var j: usize = 0;
        while (j + 1 < a.len - i) : (j += 1) {
            if (a[j] > a[j + 1]) {
                std.mem.swap(i32, &a[j], &a[j + 1]);
                swapped = true;
            }
        }
        if (!swapped) break;
    }
}

pub fn main() !void {
    const out = std.io.getStdOut().writer();
    var a = [_]i32{ 5, 2, 9, 1, 5, 6 };
    bubbleSort(&a);
    try out.writeAll("Sorted:");
    for (a) |x| try out.print(" {d}", .{x});
    try out.writeAll("\n");
}
