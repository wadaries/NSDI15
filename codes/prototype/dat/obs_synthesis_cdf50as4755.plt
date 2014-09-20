
reset
set terminal pdfcairo font "Gill Sans,9" linewidth 2 rounded fontscale 1

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
set logscale x
set key bottom right

set ylabel " Time (ms)"
set title "CDF of synthesis time for AS 4755"
set output "./dat/obs_synthesis_cdf50as4755.pdf"

plot "./dat/obs_synthesis_cdf50as4755.dat" using 2:1 title "synthesize ACL insertion" with lp ls 1,\
 '' using 3:1 title "synthesize ACL deletion" with lp ls 2,\
 '' using 4:1 title "synthesize ACL update" with lp ls 3