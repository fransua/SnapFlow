
#! /bin/bash

set -euo pipefail  # any error or undefined variable or pipefail (respectively) will stop the script



cd /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep1

SECONDS=0

touch /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep1/.running
rm -f /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep1/.error

trap 'error_handler $LINENO $?' ERR

error_handler() {
    echo $SECONDS > /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep1/.error
    rm -f /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep1/.running
    exit 1
}

DONE_FILE=/home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep1/.done

awk '/^>/{f="seq_"++d} {print > f}' < /home/fransua/Box/SnapFlow/examples/basic_pipeline/Data/sample_1.fa 2> /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep1/.command.err 1> /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep1/.command.out && echo $SECONDS > $DONE_FILE

echo split_sequences_rep1 ||  rm -f $DONE_FILE

rm -f /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep1/.running

if [[ ! -f "$DONE_FILE" ]]; then
  echo $SECONDS > /home/fransua/Box/SnapFlow/examples/basic_pipeline/basic_run/tmp/sequence_transformation/split_sequences/rep1/.error
  exit 1
fi

