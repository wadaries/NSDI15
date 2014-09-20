
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
set output "/Users/anduo/Documents/NSDI15/codes/prototype/dat/pdf_figures/datset.pdf"
set terminal pdfcairo size 8,3 font "Gill Sans,9" linewidth 2 rounded fontscale 1
# default 5 by 3 (inches)

set multiplot layout 1,3
set lmargin -2
set rmargin -3

set xtics rotate
set key top left
set ylabel "Configuration (# entries)" offset .5,0
set xlabel "Network size (# switches)"

set xrange [-2000:14000]
set yrange [5000000:14000000]

plot "/Users/anduo/Documents/NSDI15/codes/prototype/dat/datset.dat" using 2:3 pt 7 notitle,\
'' using 2:3:1:xtic(2):ytic(3) with labels offset 0,.8 notitle

set xrange [0:5]
set yrange [0:150]
set ylabel "Forwarding graph (# nodes)" offset 1,0
set xlabel "AS number"
plot "/Users/anduo/Documents/NSDI15/codes/prototype/dat/fg_size_count200.dat" using 1:3 pt 3 ps .3 notitle,\
''using 1:3:4:xtic(2) with points pointsize variable lt 1 pt 19 notitle

set ylabel "Path length (# hops)" offset 1,0
set yrange [0:50]
plot "/Users/anduo/Documents/NSDI15/codes/prototype/dat/path_len200.dat" using 1:3 pt 3 ps .3 notitle,\
''using 1:3:4:xtic(2) with points pointsize variable lt 1 pt 19 notitle
unset multiplot