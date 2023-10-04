#!/bin/bash

PY=python3


if [ $1 = "e" ]; then
  $PY tests/exp/exp_time_to_deanon_vs_num_servers.py

elif [ $1 = "em" ]; then
  $PY tests/exp/exp_time_to_deanon_vs_num_servers_w_model.py

else
  echo "Unexpected arg= $1"
fi
