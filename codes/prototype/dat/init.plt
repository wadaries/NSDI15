# gnuplot script

reset
set terminal png
set output '/Users/anduo/Documents/NSDI15/codes/prototype/dat/init.png'

# set xrange [-0.3 : 3.5]
# set xtics border in scale 1,0.5 # nomirror rotate by -30  offset character 0, 0, 0 autojustify
# set key autotitle columnhead
set logscale y

set boxwidth 0.9 relative
set style data histograms
set style histogram cluster
set style fill solid .5 border lt -1
set xtics
plot "./dat/init.dat" using 2:xticlabels(1),\
 '' using 3:xticlabels(1),\
 '' using 4:xticlabels(1)
        