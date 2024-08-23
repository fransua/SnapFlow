from sf import IO_type, rule


@rule
def split_sequences(replicate, **kwargs):
    input_  = {
        'seq_path' : IO_type('path', replicate),
        }

    output = {
        'splitted_files': f"seq_*",
        }

    cmd = f"""awk '/^>/{{f="seq_"++d}} {{print > f}}' < {input_['seq_path']}"""


@rule
def reverse(splitted, **kwargs):
    input_  = {
        'sequences': IO_type('path' , 'splitted_files', splitted),
        }

    output = {
        'reversed': "reversed.fa",
        }

    cmd = f"""
    python bin/reverse_sequences.py {input_['sequences']} {output['reversed']}
"""
