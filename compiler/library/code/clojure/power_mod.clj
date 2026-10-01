;; Быстрое возведение в степень: loop/recur с аккумулятором.
(def MOD 1000000007)

(defn power-mod [base exp m]
  (loop [b (mod base m), e exp, result 1]
    (if (zero? e)
      result
      (recur (mod (* b b) m)
             (bit-shift-right e 1)
             (if (odd? e) (mod (* result b) m) result)))))

(println (str "2^30 mod " MOD " = " (power-mod 2 30 MOD)))
(println (str "3^200 mod " MOD " = " (power-mod 3 200 MOD)))
