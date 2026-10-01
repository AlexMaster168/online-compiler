# Ханойские башни: 2^n - 1 ходов. Переносим n-1 дисков на вспомогательный стержень, n-й — на целевой.
moves = 0


def hanoi(n, source, spare, target):
    global moves
    if n == 0:
        return
    hanoi(n - 1, source, target, spare)
    print(f"Move disk {n} from {source} to {target}")
    moves += 1
    hanoi(n - 1, spare, source, target)


hanoi(3, "A", "B", "C")
print("Total moves:", moves)
