// Быстрое возведение в степень: O(log n).
const MOD: u64 = 1_000_000_007;

fn power_mod(mut base: u64, mut exp: u64, m: u64) -> u64 {
    let mut result = 1;
    base %= m;
    while exp > 0 {
        if exp & 1 == 1 {
            result = result * base % m;
        }
        base = base * base % m;
        exp >>= 1;
    }
    result
}

fn main() {
    println!("2^30 mod {MOD} = {}", power_mod(2, 30, MOD));
    println!("3^200 mod {MOD} = {}", power_mod(3, 200, MOD));
}
