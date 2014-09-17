# gnuplot script

reset
set term pdfcairo
set output '/Users/anduo/Documents/NSDI15/codes/prototype/dat/init.pdf'

set xrange [-0.3 : 3.5]
# set xtics border in scale 1,0.5 # nomirror rotate by -30  offset character 0, 0, 0 autojustify
# set key autotitle columnhead
set logscale y

set boxwidth 0.8 absolute
set style data histograms
set style histogram cluster
set style fill solid 1.00 noborder

set terminal pdfcairo font "Gill Sans,9" linewidth 4 rounded fontscale 1.0
set style line 80 lt rgb "#808080"
set style line 81 lt 0  # dashed
set style line 81 lt rgb "#808080"
set grid back linestyle 81
set border 3 back linestyle 80
set style line 1 lt rgb "#A00000" lw 2 pt 1
set style line 2 lt rgb "#00A000" lw 2 pt 6
set style line 3 lt rgb "#5060D0" lw 2 pt 2
set style line 4 lt rgb "#F25900" lw 2 pt 9
set xtics
set key top left

plot "./dat/init.dat" using 2:xticlabels(1) title "AS 4755",\
 '' using 3:xticlabels(1) title "AS 6461",\
 '' using 4:xticlabels(1) title "AS 7018" 