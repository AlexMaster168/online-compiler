(* Сортировка пузырьком на массиве (массивы в OCaml изменяемые). *)
let bubble_sort a =
  let n = Array.length a in
  let swapped = ref true in
  let i = ref 0 in
  while !swapped do
    swapped := false;
    for j = 0 to n - 2 - !i do
      if a.(j) > a.(j + 1) then begin
        let t = a.(j) in
        a.(j) <- a.(j + 1);
        a.(j + 1) <- t;
        swapped := true
      end
    done;
    incr i
  done

let () =
  let a = [| 5; 2; 9; 1; 5; 6 |] in
  bubble_sort a;
  print_endline ("Sorted: " ^ String.concat " " (Array.to_list (Array.map string_of_int a)))
