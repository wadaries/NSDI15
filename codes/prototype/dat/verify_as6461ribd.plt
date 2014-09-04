# gnuplot script
reset

    set terminal png
    set output './dat/verify_as6461ribd.png'
set title "Verification time for AS 6461 initialized with as6461ribd"

    set xrange [ -0.5 : 3.5]
    set xtics border in scale 1,0.5 nomirror rotate by -30  offset character 0, 0, 0 autojustify
    set key autotitle columnhead
    set xlabel "Verification tasks"
    set ylabel "Time (ms)"
    set style line 1 lc rgb '#0060ad' lt 1 lw 2 pt 7 ps .5   # --- blue
    set style line 2 lc rgb '#dd181f' lt 1 lw 2 pt 5 ps .5   # --- red

plot "./dat/verify_as6461ribd.dat" using 2:xtic(1) index 1 with linespoints notitle, \
''		using 2 index 2 with linespoints notitle, \
''		using 2 index 3 with linespoints notitle, \
''		using 2 index 4 with linespoints notitle, \
''		using 2 index 5 with linespoints notitle, \
''		using 2 index 6 with linespoints notitle, \
''		using 2 index 7 with linespoints notitle, \
''		using 2 index 8 with linespoints notitle, \
''		using 2 index 9 with linespoints notitle, \
''		using 2 index 10 with linespoints notitle, \
''		using 2 index 11 with linespoints notitle, \
''		using 2 index 12 with linespoints notitle, \
''		using 2 index 13 with linespoints notitle, \
''		using 2 index 14 with linespoints notitle, \
''		using 2 index 15 with linespoints notitle, \
''		using 2 index 16 with linespoints notitle, \
''		using 2 index 17 with linespoints notitle, \
''		using 2 index 18 with linespoints notitle, \
''		using 2 index 19 with linespoints notitle, \
''		using 2 index 20 with linespoints notitle, \
''		using 2 index 21 with linespoints notitle, \
''		using 2 index 22 with linespoints notitle, \
''		using 2 index 23 with linespoints notitle, \
''		using 2 index 24 with linespoints notitle, \
''		using 2 index 25 with linespoints notitle, \
''		using 2 index 26 with linespoints notitle, \
''		using 2 index 27 with linespoints notitle, \
''		using 2 index 28 with linespoints notitle, \
''		using 2 index 29 with linespoints notitle