; Быстрая сортировка (разбиение Ломуто) рекурсивной функцией quick_sort(lo, hi).
; Аргументы приходят в rdi и rsi; то, что нужно после рекурсивного вызова, храним в callee-saved регистрах.
        default rel
        global  main
        extern  printf

N       equ     7

        section .data
arr:    dq      10, 7, 8, 9, 1, 5, 3
label:  db      "Sorted:", 0
fmt_s:  db      "%s", 0
fmt_n:  db      " %ld", 0
fmt_nl: db      10, 0

        section .text
main:
        push    rbx
        xor     edi, edi
        mov     esi, N - 1
        call    quick_sort
        lea     rdi, [label]
        lea     rsi, [arr]
        mov     edx, N
        call    print_list
        pop     rbx
        xor     eax, eax
        ret

; quick_sort(rdi = lo, rsi = hi) сортирует arr[lo..hi] (индексы знаковые: hi может быть -1)
quick_sort:
        cmp     rdi, rsi
        jge     .ret
        push    rbx
        push    r12
        push    r13
        mov     r12, rdi                ; lo
        mov     r13, rsi                ; hi
        lea     r8, [arr]
        mov     rax, [r8 + r13*8]       ; опорный элемент
        mov     rcx, r12                ; i
        mov     rdx, r12                ; j
.loop:
        cmp     rdx, r13
        jge     .place
        mov     r9, [r8 + rdx*8]
        cmp     r9, rax
        jge     .next
        mov     r10, [r8 + rcx*8]       ; a[i] <-> a[j]
        mov     [r8 + rcx*8], r9
        mov     [r8 + rdx*8], r10
        inc     rcx
.next:
        inc     rdx
        jmp     .loop
.place:
        mov     r9, [r8 + rcx*8]        ; опора встаёт на место i
        mov     r10, [r8 + r13*8]
        mov     [r8 + rcx*8], r10
        mov     [r8 + r13*8], r9
        mov     rbx, rcx                ; p
        mov     rdi, r12
        lea     rsi, [rbx - 1]
        call    quick_sort              ; левая часть
        lea     rdi, [rbx + 1]
        mov     rsi, r13
        call    quick_sort              ; правая часть
        pop     r13
        pop     r12
        pop     rbx
.ret:
        ret

print_list:
        push    rbx
        push    r12
        push    r13
        mov     rbx, rsi
        mov     r12, rdx
        xor     r13d, r13d
        mov     rsi, rdi
        lea     rdi, [fmt_s]
        xor     eax, eax
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
