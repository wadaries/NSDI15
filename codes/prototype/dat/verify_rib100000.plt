# gnuplot script
reset

set terminal png
set output './dat/verify_rib100000.png'
set title "Verification time for rib100000"

set xrange [ -0.5 : 3.5]
set xtics border in scale 1,0.5 nomirror rotate by -30  offset character 0, 0, 0 autojustify
set key autotitle columnhead
set xlabel "Verification tasks"
set ylabel "Time (ms)"
set style line 1 lc rgb '#0060ad' lt 1 lw 2 pt 7 ps .5   # --- blue
set style line 2 lc rgb '#dd181f' lt 1 lw 2 pt 5 ps .5   # --- red

plot "./dat/verify_rib100000.dat" using 2:xtic(1) index 1 with linespoints notitle, \
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
''		using 2 index 29 with linespoints notitle, \
''		using 2 index 30 with linespoints notitle, \
''		using 2 index 31 with linespoints notitle, \
''		using 2 index 32 with linespoints notitle, \
''		using 2 index 33 with linespoints notitle, \
''		using 2 index 34 with linespoints notitle, \
''		using 2 index 35 with linespoints notitle, \
''		using 2 index 36 with linespoints notitle, \
''		using 2 index 37 with linespoints notitle, \
''		using 2 index 38 with linespoints notitle, \
''		using 2 index 39 with linespoints notitle, \
''		using 2 index 40 with linespoints notitle, \
''		using 2 index 41 with linespoints notitle, \
''		using 2 index 42 with linespoints notitle, \
''		using 2 index 43 with linespoints notitle, \
''		using 2 index 44 with linespoints notitle, \
''		using 2 index 45 with linespoints notitle, \
''		using 2 index 46 with linespoints notitle, \
''		using 2 index 47 with linespoints notitle, \
''		using 2 index 48 with linespoints notitle, \
''		using 2 index 49 with linespoints notitle, \
''		using 2 index 50 with linespoints notitle, \
''		using 2 index 51 with linespoints notitle, \
''		using 2 index 52 with linespoints notitle, \
''		using 2 index 53 with linespoints notitle, \
''		using 2 index 54 with linespoints notitle, \
''		using 2 index 55 with linespoints notitle, \
''		using 2 index 56 with linespoints notitle, \
''		using 2 index 57 with linespoints notitle, \
''		using 2 index 58 with linespoints notitle, \
''		using 2 index 59 with linespoints notitle, \
''		using 2 index 60 with linespoints notitle, \
''		using 2 index 61 with linespoints notitle, \
''		using 2 index 62 with linespoints notitle, \
''		using 2 index 63 with linespoints notitle, \
''		using 2 index 64 with linespoints notitle, \
''		using 2 index 65 with linespoints notitle, \
''		using 2 index 66 with linespoints notitle, \
''		using 2 index 67 with linespoints notitle, \
''		using 2 index 68 with linespoints notitle, \
''		using 2 index 69 with linespoints notitle, \
''		using 2 index 70 with linespoints notitle, \
''		using 2 index 71 with linespoints notitle, \
''		using 2 index 72 with linespoints notitle, \
''		using 2 index 73 with linespoints notitle, \
''		using 2 index 74 with linespoints notitle, \
''		using 2 index 75 with linespoints notitle, \
''		using 2 index 76 with linespoints notitle, \
''		using 2 index 77 with linespoints notitle, \
''		using 2 index 78 with linespoints notitle, \
''		using 2 index 79 with linespoints notitle, \
''		using 2 index 80 with linespoints notitle, \
''		using 2 index 81 with linespoints notitle, \
''		using 2 index 82 with linespoints notitle, \
''		using 2 index 83 with linespoints notitle, \
''		using 2 index 84 with linespoints notitle, \
''		using 2 index 85 with linespoints notitle, \
''		using 2 index 86 with linespoints notitle, \
''		using 2 index 87 with linespoints notitle, \
''		using 2 index 88 with linespoints notitle, \
''		using 2 index 89 with linespoints notitle, \
''		using 2 index 90 with linespoints notitle, \
''		using 2 index 91 with linespoints notitle, \
''		using 2 index 92 with linespoints notitle, \
''		using 2 index 93 with linespoints notitle, \
''		using 2 index 94 with linespoints notitle, \
''		using 2 index 95 with linespoints notitle, \
''		using 2 index 96 with linespoints notitle, \
''		using 2 index 97 with linespoints notitle, \
''		using 2 index 98 with linespoints notitle, \
''		using 2 index 99 with linespoints notitle