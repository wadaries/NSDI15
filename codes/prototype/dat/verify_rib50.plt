# gnuplot script
reset

    set terminal png
    set output 'test.png'
    
    set xtics border in scale 1,0.5 nomirror rotate by -45  offset character 0, 0, 0 autojustify

    set key autotitle columnhead

    set style line 1 lc rgb '#0060ad' lt 1 lw 2 pt 7 ps 1.5   # --- blue
    set style line 2 lc rgb '#dd181f' lt 1 lw 2 pt 5 ps 1.5   # --- red
plot "verify_rib50.dat" using 2:xticlabel(1) index 0 with linespoints ls 1, \
     ''		using 2 index 1 with linespoints ls 2, \
     ''		using 2 index 2 with linespoints ls 1, \
     ''		using 2 index 3 with linespoints ls 2
    