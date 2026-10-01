// НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). ~/ — целочисленное деление.
int gcd(int a, int b) => b == 0 ? a : gcd(b, a % b);
int lcm(int a, int b) => a ~/ gcd(a, b) * b;

void main() {
  print('GCD(48, 18) = ${gcd(48, 18)}');
  print('LCM(48, 18) = ${lcm(48, 18)}');
}
