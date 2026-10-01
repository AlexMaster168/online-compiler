// НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). НОК = a / gcd * b.
fn gcd(a: u64, b: u64) -> u64 {
    if b == 0 { a } else { gcd(b, a % b) }
}

fn lcm(a: u64, b: u64) -> u64 {
    a / gcd(a, b) * b
}

fn main() {
    println!("GCD(48, 18) = {}", gcd(48, 18));
    println!("LCM(48, 18) = {}", lcm(48, 18));
}
