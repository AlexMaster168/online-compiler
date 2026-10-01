// Бинарный поиск: ?usize — опциональный тип, null значит «не нашли». Полуинтервал [lo, hi).
const std = @import("std");

fn binarySearch(a: []const i32, target: i32) ?usize {
    var lo: usize = 0;
    var hi: usize = a.len;
    while (lo < hi) {
        const mid = lo + (hi - lo) / 2;
        if (a[mid] == target) return mid;
        if (a[mid] < target) lo = mid + 1 else hi = mid;
    }
    return null;
}

pub fn main() !void {
    const out = std.io.getStdOut().writer();
    const arr = [_]i32{ 1, 3, 5, 7, 9, 11, 13, 15, 17, 19 };
    for ([_]i32{ 7, 4 }) |target| {
        if (binarySearch(&arr, target)) |i| {
            try out.print("Found {d} at index {d}\n", .{ target, i });
        } else {
            try out.print("{d} not found\n", .{target});
        }
    }
}
