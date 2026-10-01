// Сортировка слиянием: всегда O(n log n), стабильная.
fn merge_sort(a: &[i32]) -> Vec<i32> {
    if a.len() <= 1 {
        return a.to_vec();
    }
    let (left, right) = a.split_at(a.len() / 2);
    let (left, right) = (merge_sort(left), merge_sort(right));
    let mut merged = Vec::with_capacity(a.len());
    let (mut i, mut j) = (0, 0);
    while i < left.len() && j < right.len() {
        if left[i] <= right[j] {
            merged.push(left[i]);
            i += 1;
        } else {
            merged.push(right[j]);
            j += 1;
        }
    }
    merged.extend_from_slice(&left[i..]);
    merged.extend_from_slice(&right[j..]);
    merged
}

fn main() {
    let sorted = merge_sort(&[38, 27, 43, 3, 9, 82, 10]);
    let out: Vec<String> = sorted.iter().map(|x| x.to_string()).collect();
    println!("Sorted: {}", out.join(" "));
}
