*> Сортировка слиянием снизу вверх: сливаем соседние серии ширины 1, 2, 4, ...
*> Рекурсия не нужна, буфер WS-B — такого же размера, как массив.
IDENTIFICATION DIVISION.
PROGRAM-ID. MERGE-SORT.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-DATA VALUE "38274303098210".
   05 WS-A PIC 99 OCCURS 7 TIMES.
01 WS-BUF.
   05 WS-B PIC 99 OCCURS 7 TIMES.
01 WS-N      PIC 9(4) VALUE 7.
01 WS-WIDTH  PIC 9(4).
01 WS-LO     PIC 9(4).
01 WS-MID    PIC 9(4).
01 WS-HI     PIC 9(4).
01 WS-I      PIC 9(4).
01 WS-J      PIC 9(4).
01 WS-K      PIC 9(4).
01 WS-OUT    PIC Z(17)9.
PROCEDURE DIVISION.
    MOVE 1 TO WS-WIDTH
    PERFORM UNTIL WS-WIDTH >= WS-N
        PERFORM VARYING WS-LO FROM 1 BY WS-WIDTH UNTIL WS-LO > WS-N
            COMPUTE WS-MID = FUNCTION MIN(WS-LO + WS-WIDTH - 1, WS-N)
            COMPUTE WS-HI = FUNCTION MIN(WS-LO + 2 * WS-WIDTH - 1, WS-N)
            MOVE WS-LO TO WS-I WS-K
            COMPUTE WS-J = WS-MID + 1
            PERFORM UNTIL WS-K > WS-HI
                IF WS-J > WS-HI OR (WS-I <= WS-MID AND WS-A(WS-I) <= WS-A(WS-J))
                    MOVE WS-A(WS-I) TO WS-B(WS-K)
                    ADD 1 TO WS-I
                ELSE
                    MOVE WS-A(WS-J) TO WS-B(WS-K)
                    ADD 1 TO WS-J
                END-IF
                ADD 1 TO WS-K
            END-PERFORM
            *> следующая пара начинается через две серии
            ADD WS-WIDTH TO WS-LO
        END-PERFORM
        MOVE WS-BUF TO WS-DATA
        MULTIPLY 2 BY WS-WIDTH
    END-PERFORM
    DISPLAY "Sorted:" WITH NO ADVANCING
    PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > WS-N
        MOVE WS-A(WS-I) TO WS-OUT
        DISPLAY " " FUNCTION TRIM(WS-OUT) WITH NO ADVANCING
    END-PERFORM
    DISPLAY SPACE
    STOP RUN.
