// Сортировка пузырьком: O(n^2). Если за проход не было обменов — массив уже отсортирован.
fn bubble_sort(a: &mut [i32]) {
    let n = a.len();
    for i in 0..n.saturating_sub(1) {
        let mut swapped = false;
        for j in 0..n - 1 - i {
            if a[j] > a[j + 1] {
                a.swap(j, j + 1);
                swapped = true;
            }
        }
        if !swapped {
            break;
        }
    }
}

fn join(a: &[i32]) -> String {
    a.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(" ")
}

fn main() {
    let mut a = [5, 2, 9, 1, 5, 6];
    bubble_sort(&mut a);
    println!("Sorted: {}", join(&a));
}
