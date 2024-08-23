import os
from sf import IO_type, rule


@rule
def count_bases(splitted, **kwargs):

    input_  = {
        'sequences': IO_type('path' , 'splitted_files', splitted),
        }

    output = {
        'stats': os.path.join(kwargs['workdir'], "stats.txt"),
        }

    cmd = f"""
for f in `ls {input_['sequences']}`;
  do 
    echo `head -n 1 $f`: `grep -v '>' $f | awk '{{print}}' ORS='' | wc -c` >> {output['stats']};
  done
echo Total sequences: `cat {input_['sequences']} | grep -v '>'| wc -l` >> {output['stats']}
echo Total bases: `cat {input_['sequences']} | grep -v '>'| wc -l` >> {output['stats']}
"""
