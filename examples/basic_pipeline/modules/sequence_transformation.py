import os
from sf import IO_type, rule


@rule
def split_sequences(replicate, **kwargs):
    input_  = {
        'seq_path' : IO_type('path', replicate),
        }

    output = {
        'splitted_files': os.path.join(kwargs['workdir'], f"seq_*"),
        }

    cmd = f"""awk '/^>/{{f="{kwargs['workdir']}/seq_"++d}} {{print > f}}' < {input_['seq_path']}"""


@rule
def reverse(splitted, **kwargs):
    input_  = {
        'sequences': IO_type('path' , 'splitted_files', splitted),
        }

    output = {
        'reversed': os.path.join(kwargs['workdir'], "reversed.fa"),
        }

    cmd = f"""
for f in `ls {input_['sequences']}`;
  do 
    head -n 1 $f >> {output['reversed']};
    grep -v '>' $f | awk '{{print}}' ORS='' | rev >> {output['reversed']};
    echo '' >> {output['reversed']};
  done
"""
