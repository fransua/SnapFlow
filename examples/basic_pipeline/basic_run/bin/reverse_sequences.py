import sys
from glob import glob


infiles = sys.argv[1]
outfile = sys.argv[2]

out = open(outfile, 'w')
for fname in glob(infiles):
    fh = open(fname)
    out.write(next(fh))
    seq = ''.join(l for l in fh)[::-1]
    out.write(f'{seq}\n')
out.close()
