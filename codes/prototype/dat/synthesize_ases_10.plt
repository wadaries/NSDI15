
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
set output "/Users/anduo/Documents/NSDI15/codes/prototype/dat/pdf_figures/synthesize_ases_10.pdf"
set terminal pdfcairo size 5,3 font "Gill Sans,9" linewidth 2 rounded fontscale 1
set multiplot layout 1,2
set lmargin -2
set rmargin -3

set key top left
set xlabel "Time (millisecond)"
set ylabel "CDF"
set logscale x

set title "obs_policy_insert"        
plot "/Users/anduo/Documents/NSDI15/codes/prototype/dat/dat/obs_policy_insert_ases_10.dat" using 3:1 with lines ls 11 title "10000",\
'' using 4:1 with lines ls 13 title "100000",\
'' using 5:1 with lines ls 14 title "300000"

set title "obs_policy_deletion"        
plot "/Users/anduo/Documents/NSDI15/codes/prototype/dat/dat/obs_policy_deletion_ases_10.dat" using 3:1 with lines ls 11 title "10000",\
'' using 4:1 with lines ls 13 title "100000",\
'' using 5:1 with lines ls 14 title "300000"
