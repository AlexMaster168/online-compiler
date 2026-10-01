# Быстрая сортировка (разбиение Ломуто) на месте.
function partition!(a, lo, hi)
    pivot = a[hi]
    i = lo
    for j in lo:hi-1
        if a[j] < pivot
            a[i], a[j] = a[j], a[i]
            i += 1
        end
    end
    a[i], a[hi] = a[hi], a[i]
    i
end

function quick_sort!(a, lo=1, hi=length(a))
    if lo < hi
        p = partition!(a, lo, hi)
        quick_sort!(a, lo, p - 1)
        quick_sort!(a, p + 1, hi)
    end
    a
end

println("Sorted: ", join(quick_sort!([10, 7, 8, 9, 1, 5, 3]), " "))
