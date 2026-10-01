;; Сортировка пузырьком на неизменяемых векторах: assoc возвращает новый вектор, оригинал цел.
(require '[clojure.string :as str])

(defn bubble-pass [v]
  (reduce (fn [[v swapped] j]
            (if (> (v j) (v (inc j)))
              [(assoc v j (v (inc j)) (inc j) (v j)) true]
              [v swapped]))
          [v false]
          (range (dec (count v)))))

(defn bubble-sort [v]
  (let [[v' swapped] (bubble-pass v)]
    (if swapped (recur v') v')))

(println (str "Sorted: " (str/join " " (bubble-sort [5 2 9 1 5 6]))))
