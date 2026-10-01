;;; Бинарный поиск по вектору: loop с изменяемыми границами, nil — «не нашли».
(defun binary-search (v target)
  (let ((lo 0) (hi (1- (length v))))
    (loop while (<= lo hi)
          do (let ((mid (floor (+ lo hi) 2)))
               (cond ((= (aref v mid) target) (return-from binary-search mid))
                     ((< (aref v mid) target) (setf lo (1+ mid)))
                     (t (setf hi (1- mid))))))
    nil))

(let ((arr #(1 3 5 7 9 11 13 15 17 19)))
  (dolist (target '(7 4))
    (let ((i (binary-search arr target)))
      (if i
          (format t "Found ~a at index ~a~%" target i)
          (format t "~a not found~%" target)))))
