#!/bin/bash

PY=python3


if [ $1 = "e" ]; then
  # $PY tests/exp/exp_perf_vs_nservers.py
  $PY tests/exp/exp_perf_vs_detection_gap_exp_factor.py

else
  echo "Unexpected arg= $1"
fi
