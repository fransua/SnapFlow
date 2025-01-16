
#! /bin/bash

set -euo pipefail  # any error or undefined variable or pipefail (respectively) will stop the script



cd /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/Sequence_stats/count_bases/rep2

SECONDS=0

touch /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/Sequence_stats/count_bases/rep2/.running
rm -f /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/Sequence_stats/count_bases/rep2/.error

trap 'error_handler $LINENO $?' ERR

error_handler() {
    echo $SECONDS > /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/Sequence_stats/count_bases/rep2/.error
    rm -f /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/Sequence_stats/count_bases/rep2/.running
    exit 1
}

DONE_FILE=/home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/Sequence_stats/count_bases/rep2/.done


for f in `ls /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep2/seq_1`;
  do 
    echo `head -n 1 $f`: `grep -v '>' $f | awk '{print}' ORS='' | wc -c` >> stats.txt;
  done
echo Total sequences: `cat /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep2/seq_1 | grep -v '>'| wc -l` >> stats.txt
echo Total bases: `cat /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep2/seq_1 | grep -v '>'| wc -l` >> stats.txt
 2> /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/Sequence_stats/count_bases/rep2/.command.err 1> /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/Sequence_stats/count_bases/rep2/.command.out && echo $SECONDS > $DONE_FILE

cp -rf stats.txt /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/results/log ||  rm -f $DONE_FILE

rm -f /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/Sequence_stats/count_bases/rep2/.running

if [[ ! -f "$DONE_FILE" ]]; then
  echo $SECONDS > /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/Sequence_stats/count_bases/rep2/.error
  exit 1
fi

