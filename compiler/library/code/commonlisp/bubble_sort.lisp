;;; Сортировка пузырьком на векторе. rotatef меняет два места местами.
(defun bubble-sort (v)
  (loop for i from 0 below (1- (length v))
        do (let ((swapped nil))
             (loop for j from 0 below (- (length v) 1 i)
                   when (> (aref v j) (aref v (1+ j)))
                     do (rotatef (aref v j) (aref v (1+ j)))
                        (setf swapped t))
             (unless swapped (return))))
  v)

;; ~{~a~^ ~} — директива format: элементы списка через пробел
(format t "Sorted: ~{~a~^ ~}~%" (coerce (bubble-sort (vector 5 2 9 1 5 6)) 'list))
