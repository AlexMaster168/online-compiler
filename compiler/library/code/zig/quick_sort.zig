// Быстрая сортировка (разбиение Ломуто) на срезах: a[0..i] и a[i + 1 ..] смотрят в тот же массив.
const std = @import("std");

fn quickSort(a: []i32) void {
    if (a.len < 2) return;
    const hi = a.len - 1;
    const pivot = a[hi];
    var i: usize = 0;
    for (0..hi) |j| {
        if (a[j] < pivot) {
            std.mem.swap(i32, &a[i], &a[j]);
            i += 1;
        }
    }
    std.mem.swap(i32, &a[i], &a[hi]);
    quickSort(a[0..i]);
    quickSort(a[i + 1 ..]);
}

pub fn main() !void {
    const out = std.io.getStdOut().writer();
    var a = [_]i32{ 10, 7, 8, 9, 1, 5, 3 };
    quickSort(&a);
    try out.writeAll("Sorted:");
    for (a) |x| try out.print(" {d}", .{x});
    try out.writeAll("\n");
}
