# Сортировка пузырьком: O(n^2). Массивы в Julia индексируются с 1; ! в имени — функция меняет аргумент.
function bubble_sort!(a)
    n = length(a)
    for i in 1:n-1
        swapped = false
        for j in 1:n-i
            if a[j] > a[j+1]
                a[j], a[j+1] = a[j+1], a[j]
                swapped = true
            end
        end
        swapped || break
    end
    a
end

println("Sorted: ", join(bubble_sort!([5, 2, 9, 1, 5, 6]), " "))
