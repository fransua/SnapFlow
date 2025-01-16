
#! /bin/bash

set -euo pipefail  # any error or undefined variable or pipefail (respectively) will stop the script



cd /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/reverse/rep2

SECONDS=0

touch /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/reverse/rep2/.running
rm -f /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/reverse/rep2/.error

trap 'error_handler $LINENO $?' ERR

error_handler() {
    echo $SECONDS > /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/reverse/rep2/.error
    rm -f /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/reverse/rep2/.running
    exit 1
}

DONE_FILE=/home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/reverse/rep2/.done


    python /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/bin/reverse_sequences.py /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep2/seq_1 reversed.fa
 2> /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/reverse/rep2/.command.err 1> /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/reverse/rep2/.command.out && echo $SECONDS > $DONE_FILE

echo reverse_rep2 ||  rm -f $DONE_FILE

rm -f /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/reverse/rep2/.running

if [[ ! -f "$DONE_FILE" ]]; then
  echo $SECONDS > /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/reverse/rep2/.error
  exit 1
fi

