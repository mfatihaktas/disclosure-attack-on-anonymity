#!/bin/bash
echo $1 $2 $3

if [ $1 = "i" ]; then
  srun --partition=main --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=8000 --time=8:00:00 --export=ALL --pty bash -i
  # srun --partition=main --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=16000 --time=12:00:00 --export=ALL --pty bash -i
  # srun --partition=main --nodes=1 --ntasks=1 --cpus-per-task=20 --mem=16000 --time=3:00:00 --export=ALL --pty bash -i

elif [ $1 = "j" ]; then
  # FILE="exp_perf_vs_num_servers"
  # FILE="exp_perf_vs_detection_gap_exp_factor"
  # FILE="exp_perf_vs_num_servers_excluded_from_threshold"
  # FILE="exp_perf_vs_prob_server_active"
  FILE="exp_perf_vs_max_delivery_time_for_adversary"

  NTASKS=1
  echo "#!/bin/bash
#SBATCH --partition=main             # Partition (job queue)
#SBATCH --job-name=${FILE}
#SBATCH --nodes=${NTASKS}            # Number of nodes you require
#SBATCH --ntasks=${NTASKS}           # Total # of tasks across all nodes
#SBATCH --cpus-per-task=1            # Cores per task (>1 if multithread tasks)
#SBATCH --mem=8000                   # Real memory (RAM) required (MB)
#SBATCH --time=48:00:00              # Total run time limit (HH:MM:SS)
#SBATCH --export=ALL                 # Export your current env to the job env
#SBATCH --output=log/${FILE}.%N.%j.out
#SBATCH --error=log/${FILE}.%N.%j.err
#SBATCH -o log/srun.out

cd ${HOME}/disclosure-attack-on-anonymity

srun python ${PWD}/tests/exp/${FILE}.py
  " > job_script.sh

  # rm log/*
  sbatch job_script.sh

elif [ $1 = "l" ]; then
  squeue -u mfa51

elif [ $1 = "k" ]; then
  scancel --user=mfa51 # -n learning

elif [ $1 = "node" ]; then
  sinfo --Node # --format="%n %f %c %m %G"

else
  echo "Unexpected arg= $1"
fi
