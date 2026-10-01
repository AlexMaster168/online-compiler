; Наибольшая общая подпоследовательность: таблица dp[8][7] из qword, dp[i][j] по адресу dp + (i*7 + j)*8.
        default rel
        global  main
        extern  printf

LA      equ     7                       ; длина "ABCBDAB"
LB      equ     6                       ; длина "BDCABA"
COLS    equ     LB + 1

        section .data
a:      db      "ABCBDAB"
b:      db      "BDCABA"
fmt:    db      "LCS(ABCBDAB, BDCABA) = %ld", 10, 0

        section .bss
dp:     resq    (LA + 1) * COLS         ; .bss обнулён — первая строка и столбец уже нули

        section .text
main:
        push    rbx
        lea     r8, [dp]
        lea     r9, [a]
        lea     r10, [b]
        mov     ecx, 1                  ; i
.row:
        cmp     rcx, LA
        jg      .done
        mov     edx, 1                  ; j
.cell:
        cmp     rdx, LB
        jg      .row_next
        imul    r11, rcx, COLS
        add     r11, rdx                ; индекс клетки (i, j)
        mov     al, [r9 + rcx - 1]
        cmp     al, [r10 + rdx - 1]
        jne     .differ
        mov     rax, [r8 + r11*8 - (COLS + 1) * 8]      ; dp[i-1][j-1]
        inc     rax
        jmp     .store
.differ:
        mov     rax, [r8 + r11*8 - COLS * 8]            ; dp[i-1][j]
        mov     rsi, [r8 + r11*8 - 8]                   ; dp[i][j-1]
        cmp     rax, rsi
        cmovl   rax, rsi
.store:
        mov     [r8 + r11*8], rax
        inc     rdx
        jmp     .cell
.row_next:
        inc     rcx
        jmp     .row
.done:
        lea     rdi, [fmt]
        mov     rsi, [r8 + (LA * COLS + LB) * 8]
        xor     eax, eax
        call    printf wrt ..plt
        pop     rbx
        xor     eax, eax
        ret

        section .note.GNU-stack noalloc noexec nowrite progbits
