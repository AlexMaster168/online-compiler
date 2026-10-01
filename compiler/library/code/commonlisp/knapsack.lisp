;;; Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; c идёт сверху вниз (downfrom).
(defun knapsack (items capacity)
  (let ((dp (make-array (1+ capacity) :initial-element 0)))
    (loop for (w v) in items
          do (loop for c from capacity downto w
                   do (setf (aref dp c) (max (aref dp c) (+ (aref dp (- c w)) v)))))
    (aref dp capacity)))

(format t "Knapsack max value: ~a~%" (knapsack '((1 1) (3 4) (4 5) (5 7)) 7))
