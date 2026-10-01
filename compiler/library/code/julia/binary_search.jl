# Бинарный поиск: O(log n). nothing — «не нашли». Индексы печатаем с 0, как другие языки.
function binary_search(a, target)
    lo, hi = 1, length(a)
    while lo <= hi
        mid = (lo + hi) ÷ 2
        a[mid] == target && return mid - 1
        if a[mid] < target
            lo = mid + 1
        else
            hi = mid - 1
        end
    end
    nothing
end

arr = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
for target in (7, 4)
    i = binary_search(arr, target)
    println(i === nothing ? "$target not found" : "Found $target at index $i")
end
