#!/bin/bash

PY=python3


if [ $1 = "e" ]; then
  $PY tests/exp/exp_time_to_deanon_vs_num_servers.py

else
  echo "Unexpected arg= $1"
fi
