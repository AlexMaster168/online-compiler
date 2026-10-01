// Быстрая сортировка (разбиение Ломуто) на срезах: split_at_mut делит массив без копий.
fn partition(a: &mut [i32]) -> usize {
    let hi = a.len() - 1;
    let pivot = a[hi];
    let mut i = 0;
    for j in 0..hi {
        if a[j] < pivot {
            a.swap(i, j);
            i += 1;
        }
    }
    a.swap(i, hi);
    i
}

fn quick_sort(a: &mut [i32]) {
    if a.len() < 2 {
        return;
    }
    let p = partition(a);
    let (left, right) = a.split_at_mut(p);
    quick_sort(left);
    quick_sort(&mut right[1..]);
}

fn main() {
    let mut a = [10, 7, 8, 9, 1, 5, 3];
    quick_sort(&mut a);
    let out: Vec<String> = a.iter().map(|x| x.to_string()).collect();
    println!("Sorted: {}", out.join(" "));
}
