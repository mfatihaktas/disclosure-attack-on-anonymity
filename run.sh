#!/bin/bash

PY=python3


if [ $1 = "e" ]; then
  # $PY tests/exp/exp_perf_vs_num_servers.py
  # $PY tests/exp/exp_perf_vs_detection_gap_exp_factor.py
  # $PY tests/exp/exp_perf_vs_num_servers_excluded_from_threshold.py
  # $PY tests/exp/exp_perf_vs_prob_server_active.py
  # $PY tests/exp/exp_perf_vs_max_delivery_time_for_adversary.py
  $PY tests/exp/exp_perf_vs_max_delivery_time.py
  # $PY tests/exp/exp_trials_over_channels.py

else
  echo "Unexpected arg= $1"
fi
