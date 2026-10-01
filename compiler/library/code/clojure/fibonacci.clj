;; Числа Фибоначчи ленивой последовательностью iterate: каждая пара (a, b) -> (b, a + b).
(require '[clojure.string :as str])

(def fibs (map first (iterate (fn [[a b]] [b (+' a b)]) [0 1])))

(println (str "Fibonacci: " (str/join " " (take 15 fibs))))
(println (str "F(50) = " (nth fibs 50)))
