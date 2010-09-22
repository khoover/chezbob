# gnuplot script for generating plots summarizing Chez Bob finances
#
# This script assumes that the file "accounts.data" in the current directory
# contains a summary dump containing daily finance account balances.  It
# generates a PostScript file (finances.ps) containing all the graphs.

set xdata time
set timefmt "%Y-%m-%d"
set xlabel "Date"
set ylabel "Amount ($)"
set key top left
set grid
set xzeroaxis lt -1

set term postscript solid color font 12
set output "finances.ps"

set title "Overall Snapshot: ChezBob Net Non-Restricted Assets"
plot "accounts.data" using 1:($28-$31-$24-$25) with linespoints \
        title "Net Assets", \
     "accounts.data" using 1:34 with lines title "Potential Bad Debt", \
     "accounts.data" using 1:($28-$31-$24-$25+$35) with lines \
        title "Including Inventory"

set title "Inventory: Valued at Cost"
plot "accounts.data" using 1:35 with linespoints notitle

set title "Bank of Bob Operations: Positive vs. Negative Deposits"
plot "accounts.data" using 1:33 with lines title "Positive (Deposits)", \
     "accounts.data" using 1:34 with lines title "Negative (Debt)", \
     "accounts.data" using 1:6 with lines title "Net"

set title "Cash on Hand: Available Cash and Bank Balances"
plot "accounts.data" using 1:5 with steps title "Bank Account", \
     "accounts.data" using 1:($5+$8+$9) with lines title "Bank Account + Cash"

set title "Monthly Sales"
plot "monthly.data" using 1:10 with boxes fill fs solid 0.3 notitle
