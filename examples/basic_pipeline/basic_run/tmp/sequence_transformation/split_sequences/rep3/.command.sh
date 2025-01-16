
#! /bin/bash

set -euo pipefail  # any error or undefined variable or pipefail (respectively) will stop the script



cd /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep3

SECONDS=0

touch /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep3/.running
rm -f /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep3/.error

trap 'error_handler $LINENO $?' ERR

error_handler() {
    echo $SECONDS > /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep3/.error
    rm -f /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep3/.running
    exit 1
}

DONE_FILE=/home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep3/.done

awk '/^>/{f="seq_"++d} {print > f}' < /home/fransua/Box/SnapFlow/examples/basic_pipeline/Data/sample_3.fa 2> /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep3/.command.err 1> /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep3/.command.out && echo $SECONDS > $DONE_FILE

echo split_sequences_rep3 ||  rm -f $DONE_FILE

rm -f /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep3/.running

if [[ ! -f "$DONE_FILE" ]]; then
  echo $SECONDS > /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep3/.error
  exit 1
fi

