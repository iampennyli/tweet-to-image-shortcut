# usage: render.sh data.json out.png
python3 fill.py $1 f.html $3 >/tmp/est || exit 1; H=$(awk '{print $2}' /tmp/est)
need=$(google-chrome --headless=new --no-sandbox --disable-gpu --dump-dom file://$PWD/f.html 2>/dev/null | rg -o 'data-need="[0-9_.]+"')
echo "estimate=$H actual_needed=$need"
google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars --window-size=1080,$H --screenshot=$2 file://$PWD/f.html 2>/dev/null
google-chrome --headless=new --no-sandbox --disable-gpu --no-pdf-header-footer --print-to-pdf=/tmp/t.pdf file://$PWD/f.html 2>/dev/null; pdfinfo /tmp/t.pdf | rg "Pages|Page size"
