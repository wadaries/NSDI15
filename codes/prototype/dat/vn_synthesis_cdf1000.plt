
reset
set terminal pdfcairo font "Gill Sans,9" linewidth 2 rounded fontscale 1

set logscale y

set style line 80 lt rgb "#808080"
set style line 81 lt 0  # dashed
set style line 81 lt rgb "#808080"
set grid back linestyle 81
set border 3 back linestyle 80

set style line 1 lt rgb "#A00000" lw 1 pt 1 ps 1
set style line 2 lt rgb "#00A000" lw 1 pt 6 ps 1
set style line 3 lt rgb "#5060D0" lw 1 pt 2 ps 1
set style line 4 lt rgb "#F25900" lw 1 pt 9 ps 1

set xtics nomirror
set ytics nomirror
set key bottom right

set ylabel "Cumulative distribution of time (ms)"
set output "./dat/vn_synthesis_cdf1000.pdf"

plot "./dat/vn_synthesis_cdf1000.dat" using 2 title "synthesize policy deletion" with lp ls 1,\
 '' using 3 title "synthesize policy insertion" with lp ls 2,\
 '' using 4 title "synthesize policy update" with lp ls 3,\
 '' using 5 title "compute per-switch configuration delta" with lp ls 4