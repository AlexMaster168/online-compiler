;; Факториал рекурсией. *' — умножение с автоматическим переходом на BigInt.
(defn factorial [n]
  (if (<= n 1) 1 (*' n (factorial (dec n)))))

(println (str "10! = " (factorial 10)))
(println (str "20! = " (factorial 20)))
