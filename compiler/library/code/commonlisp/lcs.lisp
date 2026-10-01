;;; Наибольшая общая подпоследовательность: двумерный массив dp, char= сравнивает символы.
(defun lcs (a b)
  (let ((dp (make-array (list (1+ (length a)) (1+ (length b))) :initial-element 0)))
    (loop for i from 1 to (length a)
          do (loop for j from 1 to (length b)
                   do (setf (aref dp i j)
                            (if (char= (char a (1- i)) (char b (1- j)))
                                (1+ (aref dp (1- i) (1- j)))
                                (max (aref dp (1- i) j) (aref dp i (1- j)))))))
    (aref dp (length a) (length b))))

(format t "LCS(ABCBDAB, BDCABA) = ~a~%" (lcs "ABCBDAB" "BDCABA"))
