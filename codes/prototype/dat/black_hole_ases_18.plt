
reset

set style line 80 lt -1 lc rgb "#808080"
set style line 81 lt 0  # dashed
set style line 81 lt rgb "#808080"
set grid back linestyle 81
set border 3 back linestyle 80

set style line 1 lt rgb "#A00000" lw 1 pt 1 ps 1
set style line 2 lt rgb "#00A000" lw 1 pt 6 ps 1
set style line 3 lt rgb "#5060D0" lw 1 pt 2 ps 1
set style line 4 lt rgb "#F25900" lw 1 pt 9 ps 1

set termoption dashed
set style line 11 lt rgb "#A00000" lw 3 
set style line 12 lt rgb "#00A000" lw 3
set style line 13 lt rgb "#5060D0" lw 3
set style line 14 lt rgb "#F25900" lw 3

set xtics nomirror
set ytics nomirror
set output "/Users/anduo/Documents/NSDI15/codes/prototype/dat/pdf_figures/black_hole_ases_18.pdf"
set terminal pdfcairo font "Gill Sans,9" linewidth 2 rounded fontscale 1

set key top left
set xlabel "Time (millisecond)"
set ylabel "CDF"
set logscale x

plot "/Users/anduo/Documents/NSDI15/codes/prototype/dat/black_hole_ases_18.dat" using 2:1 with lines ls 11 title "AS4755",\
'' using 4:1 with lines ls 13 title "AS3356",\
'' using 5:1 with lines ls 14 title "AS2914",\
'' using 3:1 with lines ls 12 title "AS7018"