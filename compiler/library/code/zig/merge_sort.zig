// Сортировка слиянием: буфер той же длины передаём вниз по рекурсии, без выделений в куче.
const std = @import("std");

fn mergeSort(a: []i32, buf: []i32) void {
    if (a.len < 2) return;
    const mid = a.len / 2;
    mergeSort(a[0..mid], buf[0..mid]);
    mergeSort(a[mid..], buf[mid..]);
    var i: usize = 0;
    var j: usize = mid;
    for (0..a.len) |k| {
        if (j >= a.len or (i < mid and a[i] <= a[j])) {
            buf[k] = a[i];
            i += 1;
        } else {
            buf[k] = a[j];
            j += 1;
        }
    }
    @memcpy(a, buf[0..a.len]);
}

pub fn main() !void {
    const out = std.io.getStdOut().writer();
    var a = [_]i32{ 38, 27, 43, 3, 9, 82, 10 };
    var buf: [a.len]i32 = undefined;
    mergeSort(&a, &buf);
    try out.writeAll("Sorted:");
    for (a) |x| try out.print(" {d}", .{x});
    try out.writeAll("\n");
}
