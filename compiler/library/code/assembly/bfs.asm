; Поиск в ширину: очередь — массив queue с индексами head/tail, соседи — по два на вершину.
        default rel
        global  main
        extern  printf

V       equ     6

        section .data
adj:    dq      1, 2,  0, 3,  0, 4,  1, 5,  2, 5,  3, 4
dist:   dq      -1, -1, -1, -1, -1, -1
l_ord:  db      "BFS order:", 0
l_dist: db      "Distances:", 0
fmt_s:  db      "%s", 0
fmt_n:  db      " %ld", 0
fmt_nl: db      10, 0

        section .bss
queue:  resq    V

        section .text
main:
        push    rbx
        lea     r8, [adj]
        lea     r9, [dist]
        lea     r10, [queue]
        mov     qword [r9], 0           ; dist[0] = 0
        mov     qword [r10], 0          ; queue = [0]
        xor     ecx, ecx                ; head
        mov     edx, 1                  ; tail
.loop:
        cmp     rcx, rdx
        jge     .print
        mov     rax, [r10 + rcx*8]      ; v
        inc     rcx
        xor     r11d, r11d              ; k
.neighbours:
        cmp     r11, 2
        jge     .loop
        lea     rsi, [rax*2 + r11]
        mov     rsi, [r8 + rsi*8]       ; u
        cmp     qword [r9 + rsi*8], -1
        jne     .skip
        mov     rdi, [r9 + rax*8]
        inc     rdi
        mov     [r9 + rsi*8], rdi       ; dist[u] = dist[v] + 1
        mov     [r10 + rdx*8], rsi
        inc     rdx
.skip:
        inc     r11
        jmp     .neighbours
.print:
        lea     rdi, [l_ord]
        lea     rsi, [queue]            ; порядок обхода — это и есть очередь
        mov     edx, V
        call    print_list
        lea     rdi, [l_dist]
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
