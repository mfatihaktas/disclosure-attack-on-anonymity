#!/bin/bash

PY=python3


if [ $1 = "e" ]; then
  $PY tests/exp/exp_perf_vs_nservers.py
  # $PY tests/exp/exp_perf_vs_max_stdev.py

else
  echo "Unexpected arg= $1"
fi
