# gnuplot script
reset

set terminal png
set output './dat/verify_rib60.png'
set xrange [ -0.5 : 4.5]
set xtics border in scale 1,0.5 nomirror rotate by -45  offset character 0, 0, 0 autojustify

set key autotitle columnhead

set style line 1 lc rgb '#0060ad' lt 1 lw 2 pt 7 ps 1.5   # --- blue
set style line 2 lc rgb '#dd181f' lt 1 lw 2 pt 5 ps 1.5   # --- red

plot "./dat/verify_rib60.dat" using 2:xticlabel(1) index 0, \
''		using 2 index 1 ls 2, \
''		using 2 index 2 ls 2, \
''		using 2 index 3 ls 2, \
''		using 2 index 4 ls 2, \
''		using 2 index 5 ls 2, \
''		using 2 index 6 ls 2, \
''		using 2 index 7 ls 2, \
''		using 2 index 8 ls 2, \
''		using 2 index 9 ls 2, \
''		using 2 index 10 ls 2, \
''		using 2 index 11 ls 2, \
''		using 2 index 12 ls 2, \
''		using 2 index 13 ls 2, \
''		using 2 index 14 ls 2, \
''		using 2 index 15 ls 2, \
''		using 2 index 16 ls 2, \
''		using 2 index 17 ls 2, \
''		using 2 index 18 ls 2, \
''		using 2 index 19 ls 2