# Сортировка слиянием: срезы a[1:mid] копируют, @view — нет. Всегда O(n log n).
function merge_sort(a)
    length(a) <= 1 && return a
    mid = length(a) ÷ 2
    left = merge_sort(a[1:mid])
    right = merge_sort(a[mid+1:end])
    merged = similar(a, 0)
    i = j = 1
    while i <= length(left) && j <= length(right)
        if left[i] <= right[j]
            push!(merged, left[i]); i += 1
        else
            push!(merged, right[j]); j += 1
        end
    end
    vcat(merged, left[i:end], right[j:end])
end

println("Sorted: ", join(merge_sort([38, 27, 43, 3, 9, 82, 10]), " "))
