*> Наибольшая общая подпоследовательность: таблица DP размером 8 x 7 (строка и столбец 1 — нули).
*> Ссылочная модификация WS-A(I:1) — I-й символ строки.
IDENTIFICATION DIVISION.
PROGRAM-ID. LCS.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 WS-A      PIC X(7) VALUE "ABCBDAB".
01 WS-B      PIC X(6) VALUE "BDCABA".
01 WS-TABLE.
   05 WS-ROW OCCURS 8 TIMES.
      10 WS-DP PIC 99 OCCURS 7 TIMES VALUE 0.
01 WS-I      PIC 99.
01 WS-J      PIC 99.
01 WS-OUT    PIC Z(17)9.
PROCEDURE DIVISION.
    PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > 7
        PERFORM VARYING WS-J FROM 1 BY 1 UNTIL WS-J > 6
            IF WS-A(WS-I:1) = WS-B(WS-J:1)
                COMPUTE WS-DP(WS-I + 1, WS-J + 1) = WS-DP(WS-I, WS-J) + 1
            ELSE
                COMPUTE WS-DP(WS-I + 1, WS-J + 1) =
                    FUNCTION MAX(WS-DP(WS-I, WS-J + 1), WS-DP(WS-I + 1, WS-J))
            END-IF
        END-PERFORM
    END-PERFORM
    MOVE WS-DP(8, 7) TO WS-OUT
    DISPLAY "LCS(ABCBDAB, BDCABA) = " FUNCTION TRIM(WS-OUT)
    STOP RUN.
