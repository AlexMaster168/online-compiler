; Сортировка пузырьком на x86-64 (NASM, Linux, System V ABI). Печать — через printf из libc.
; Числа — 64-битные (dq), элемент i лежит по адресу arr + i*8.
        default rel
        global  main
        extern  printf

N       equ     6

        section .data
arr:    dq      5, 2, 9, 1, 5, 6
label:  db      "Sorted:", 0
fmt_s:  db      "%s", 0
fmt_n:  db      " %ld", 0
fmt_nl: db      10, 0

        section .text
main:
        push    rbx                     ; нечётное число push-ей -> стек выровнен на 16 перед call
        lea     rbx, [arr]
        xor     r8d, r8d                ; i = 0
.outer:
        cmp     r8, N - 1
        jge     .print
        xor     r10d, r10d              ; swapped = 0
        xor     r9d, r9d                ; j = 0
        mov     r11, N - 1
        sub     r11, r8                 ; j < N - 1 - i
.inner:
        cmp     r9, r11
        jge     .pass_done
        mov     rax, [rbx + r9*8]
        mov     rdx, [rbx + r9*8 + 8]
        cmp     rax, rdx
        jle     .no_swap
        mov     [rbx + r9*8], rdx       ; обмен соседей
        mov     [rbx + r9*8 + 8], rax
        mov     r10d, 1
.no_swap:
        inc     r9
        jmp     .inner
.pass_done:
        test    r10d, r10d              ; обменов не было — массив отсортирован
        jz      .print
        inc     r8
        jmp     .outer
.print:
        lea     rdi, [label]
        mov     rsi, rbx
        mov     edx, N
        call    print_list
        pop     rbx
        xor     eax, eax
        ret

; print_list(rdi = подпись, rsi = адрес массива, rdx = количество): "подпись 1 2 3\n"
; rbx, r12, r13 — callee-saved: printf их не испортит
print_list:
        push    rbx
        push    r12
        push    r13
        mov     rbx, rsi
        mov     r12, rdx
        xor     r13d, r13d
        mov     rsi, rdi
        lea     rdi, [fmt_s]
        xor     eax, eax                ; у variadic-функций al = число векторных аргументов
        call    printf wrt ..plt
.loop:
        cmp     r13, r12
        jge     .end
        lea     rdi, [fmt_n]
        mov     rsi, [rbx + r13*8]
        xor     eax, eax
        call    printf wrt ..plt
        inc     r13
        jmp     .loop
.end:
        lea     rdi, [fmt_nl]
        xor     eax, eax
        call    printf wrt ..plt
        pop     r13
        pop     r12
        pop     rbx
        ret

        section .note.GNU-stack noalloc noexec nowrite progbits
