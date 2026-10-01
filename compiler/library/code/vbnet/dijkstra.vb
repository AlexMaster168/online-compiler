' Дейкстра с PriorityQueue (.NET 6+): O((V + E) log V).
Imports System.Collections.Generic

Module Program
    Sub Main()
        ' Поле не назвать To: это ключевое слово VB (For i = 0 To n)
        Dim graph As (Dest As Integer, W As Integer)()() = {
            New (Integer, Integer)() {(1, 4), (2, 1)},
            New (Integer, Integer)() {(3, 1)},
            New (Integer, Integer)() {(1, 2), (3, 5)},
            New (Integer, Integer)() {(4, 3)},
            New (Integer, Integer)() {}
        }
        Dim dist(graph.Length - 1) As Integer
        For i As Integer = 0 To dist.Length - 1
            dist(i) = Integer.MaxValue
        Next
        dist(0) = 0
        Dim pq As New PriorityQueue(Of Integer, Integer)
        pq.Enqueue(0, 0)
        Dim v As Integer, d As Integer
        While pq.TryDequeue(v, d)
            If d > dist(v) Then Continue While  ' устаревшая запись
            For Each edge In graph(v)
                If d + edge.W < dist(edge.Dest) Then
                    dist(edge.Dest) = d + edge.W
                    pq.Enqueue(edge.Dest, dist(edge.Dest))
                End If
            Next
        End While
        Console.WriteLine("Dijkstra from 0: " & String.Join(" ", dist))
    End Sub
End Module
