;;; Ханойские башни: функция возвращает число ходов, печатая их по пути.
(defun hanoi (n source spare target)
  (if (zerop n)
      0
      (let ((before (hanoi (1- n) source target spare)))
        (format t "Move disk ~a from ~a to ~a~%" n source target)
        (+ before 1 (hanoi (1- n) spare source target)))))

(format t "Total moves: ~a~%" (hanoi 3 "A" "B" "C"))
