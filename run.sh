#!/bin/bash

PY=python3


if [ $1 = "e" ]; then
  $PY tests/exp/exp_perf_vs_num_servers.py

elif [ $1 = "em" ]; then
  $PY tests/exp/exp_perf_vs_nservers_w_model.py

else
  echo "Unexpected arg= $1"
fi
