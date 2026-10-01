// Бинарный поиск: O(log n). Option<usize> вместо магического -1. (У срезов есть .binary_search().)
use std::cmp::Ordering;

fn binary_search(a: &[i32], target: i32) -> Option<usize> {
    let (mut lo, mut hi) = (0usize, a.len());  // полуинтервал [lo, hi)
    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        match a[mid].cmp(&target) {
            Ordering::Equal => return Some(mid),
            Ordering::Less => lo = mid + 1,
            Ordering::Greater => hi = mid,
        }
    }
    None
}

fn main() {
    let a = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19];
    for target in [7, 4] {
        match binary_search(&a, target) {
            Some(i) => println!("Found {target} at index {i}"),
            None => println!("{target} not found"),
        }
    }
}
