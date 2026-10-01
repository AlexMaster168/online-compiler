; Рюкзак 0/1: dp[c] — лучшая ценность при вместимости c; внутренний цикл идёт по c сверху вниз.
        default rel
        global  main
        extern  printf

ITEMS   equ     4
CAP     equ     7

        section .data
weights: dq     1, 3, 4, 5
values:  dq     1, 4, 5, 7
fmt:     db     "Knapsack max value: %ld", 10, 0

        section .bss
dp:     resq    CAP + 1

        section .text
main:
        push    rbx
        lea     r8, [dp]
        lea     r9, [weights]
        lea     r10, [values]
        xor     ecx, ecx                ; i
.item:
        cmp     rcx, ITEMS
        jge     .done
        mov     r11, [r9 + rcx*8]       ; w
        mov     rdx, CAP                ; c
.cap:
        cmp     rdx, r11
        jl      .item_next
        mov     rax, rdx
        sub     rax, r11
        mov     rax, [r8 + rax*8]       ; dp[c - w]
        add     rax, [r10 + rcx*8]      ; + v
        cmp     rax, [r8 + rdx*8]
        jle     .cap_next
        mov     [r8 + rdx*8], rax
.cap_next:
        dec     rdx
        jmp     .cap
.item_next:
        inc     rcx
        jmp     .item
.done:
        lea     rdi, [fmt]
        mov     rsi, [r8 + CAP * 8]
        xor     eax, eax
        call    printf wrt ..plt
        pop     rbx
        xor     eax, eax
        ret

        section .note.GNU-stack noalloc noexec nowrite progbits
