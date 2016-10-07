host='https://cgit.freedesktop.org/'

for folder in `curl -s $host/libreoffice/dictionaries/tree/ | grep 'ls-dir' | cut -d "'" -f 6`; do
    for file in `curl -s $host$folder | grep 'ls-blob' | grep 'hyph_.*\.dic' | cut -d "'" -f 6`; do
        wget -N `echo $host$file | sed 's/tree/plain/'`
    done
done
