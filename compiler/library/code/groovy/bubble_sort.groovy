// Сортировка пузырьком: Groovy — скриптовый JVM-язык, класс и main не обязательны.
def bubbleSort(List<Integer> input) {
    def a = new ArrayList<Integer>(input)
    for (i in 0..<(a.size() - 1)) {
        boolean swapped = false
        for (j in 0..<(a.size() - 1 - i)) {
            if (a[j] > a[j + 1]) {
                a.swap(j, j + 1)
                swapped = true
            }
        }
        if (!swapped) break
    }
    a
}

println "Sorted: ${bubbleSort([5, 2, 9, 1, 5, 6]).join(' ')}"
