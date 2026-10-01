# НОД по Евклиду: gcd(a, b) = gcd(b, a mod b). НОК = a / gcd * b (делим первым — меньше риск переполнения).


def gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def lcm(a, b):
    return a // gcd(a, b) * b


print(f"GCD(48, 18) = {gcd(48, 18)}")
print(f"LCM(48, 18) = {lcm(48, 18)}")
