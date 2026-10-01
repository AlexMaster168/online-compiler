; Дейкстра за O(V^2) на матрице весов 5x5 (0 — нет ребра): элемент [v][u] лежит по адресу w + (v*5 + u)*8.
        default rel
        global  main
        extern  printf

V       equ     5
INF     equ     1000000000

        section .data
w:      dq      0, 4, 1, 0, 0
        dq      0, 0, 0, 1, 0
        dq      0, 2, 0, 5, 0
        dq      0, 0, 0, 0, 3
        dq      0, 0, 0, 0, 0
dist:   dq      0, INF, INF, INF, INF
label:  db      "Dijkstra from 0:", 0
fmt_s:  db      "%s", 0
fmt_n:  db      " %ld", 0
fmt_nl: db      10, 0

        section .bss
done:   resb    V

        section .text
main:
        push    rbx
        lea     r8, [w]
        lea     r9, [dist]
        lea     r10, [done]
        xor     ebx, ebx                ; шаг
.step:
        cmp     rbx, V
        jge     .print
        mov     rax, -1                 ; лучшая вершина
        xor     ecx, ecx
.pick:
        cmp     rcx, V
        jge     .picked
        cmp     byte [r10 + rcx], 0
        jne     .pick_next
        cmp     rax, -1
        je      .take
        mov     rdx, [r9 + rcx*8]
        cmp     rdx, [r9 + rax*8]
        jge     .pick_next
.take:
        mov     rax, rcx
.pick_next:
        inc     rcx
        jmp     .pick
.picked:
        cmp     qword [r9 + rax*8], INF
        je      .print                  ; остальные недостижимы
        mov     byte [r10 + rax], 1
        imul    r11, rax, V * 8         ; адрес строки матрицы
        add     r11, r8
        xor     ecx, ecx                ; u
.relax:
        cmp     rcx, V
        jge     .step_next
        mov     rdx, [r11 + rcx*8]      ; вес ребра v -> u
        test    rdx, rdx
        jz      .relax_next
        add     rdx, [r9 + rax*8]
        cmp     rdx, [r9 + rcx*8]
        jge     .relax_next
        mov     [r9 + rcx*8], rdx
.relax_next:
        inc     rcx
        jmp     .relax
.step_next:
        inc     rbx
        jmp     .step
.print:
        lea     rdi, [label]
        lea     rsi, [dist]
        mov     edx, V
        call    print_list
        pop     rbx
        xor     eax, eax
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
