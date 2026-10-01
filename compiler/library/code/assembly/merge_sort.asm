; Сортировка слиянием: merge_sort(lo, hi) сортирует полуинтервал [lo, hi), буфер tmp — в .bss.
        default rel
        global  main
        extern  printf

N       equ     7

        section .data
arr:    dq      38, 27, 43, 3, 9, 82, 10
label:  db      "Sorted:", 0
fmt_s:  db      "%s", 0
fmt_n:  db      " %ld", 0
fmt_nl: db      10, 0

        section .bss
tmp:    resq    N

        section .text
main:
        push    rbx
        xor     edi, edi
        mov     esi, N
        call    merge_sort
        lea     rdi, [label]
        lea     rsi, [arr]
        mov     edx, N
        call    print_list
        pop     rbx
        xor     eax, eax
        ret

merge_sort:
        mov     rax, rsi
        sub     rax, rdi
        cmp     rax, 2                  ; меньше двух элементов — уже отсортировано
        jl      .ret
        push    rbx
        push    r12
        push    r13
        mov     r12, rdi                ; lo
        mov     r13, rsi                ; hi
        lea     rbx, [rdi + rsi]
        shr     rbx, 1                  ; mid
        mov     rdi, r12
        mov     rsi, rbx
        call    merge_sort
        mov     rdi, rbx
        mov     rsi, r13
        call    merge_sort
        lea     r10, [arr]
        lea     r11, [tmp]
        mov     rcx, r12                ; i — по левой половине
        mov     rdx, rbx                ; j — по правой
        mov     r8, r12                 ; k — по буферу
.merge:
        cmp     r8, r13
        jge     .copy
        cmp     rcx, rbx
        jge     .right                  ; левая кончилась
        cmp     rdx, r13
        jge     .left                   ; правая кончилась
        mov     rax, [r10 + rcx*8]
        cmp     rax, [r10 + rdx*8]
        jg      .right
.left:
        mov     rax, [r10 + rcx*8]
        mov     [r11 + r8*8], rax
        inc     rcx
        jmp     .next
.right:
        mov     rax, [r10 + rdx*8]
        mov     [r11 + r8*8], rax
        inc     rdx
.next:
        inc     r8
        jmp     .merge
.copy:
        mov     r8, r12
.copy_loop:
        cmp     r8, r13
        jge     .done
        mov     rax, [r11 + r8*8]
        mov     [r10 + r8*8], rax
        inc     r8
        jmp     .copy_loop
.done:
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
