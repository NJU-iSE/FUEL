#!/bin/bash
# unset proxy settings (specified settings for deepseek)
unset http_proxy
unset https_proxy
unset all_proxy
unset HTTP_PROXY 
unset HTTPS_PROXY
unset ALL_PROXY

# fuzzing pytorch with SA and two server model
python -m fuel.fuzz --lib pytorch run_fuzz --heuristic SA --diff_type cpu_compiler --max_round 1000
#(--diff_type hardware cpu_compiler,cuda_compiler)

# ablations

# fuzzing pytorch without heuristic
# python fuel/fuzz.py --lib pytorch run_fuzz --heuristic None
# fuzzing pytorch without als
# python fuel/ablation_fuzz.py --lib pytorch --gen_prompt_config config/ablations/wo_als/gen_prompt run_fuzz --ablation wo_als --heuristic SA --max_round 3000

# fuzzing pytorch without coverage
#python fuel/ablation_fuzz.py --lib pytorch --gen_prompt_config config/ablations/wo_coverage/gen_prompt run_fuzz --ablation wo_cov --heuristic SA --max_round 3000

# fuzzing pytorch without exception
# python fuel/ablation_fuzz.py --lib pytorch --gen_prompt_config config/ablations/wo_exception/gen_prompt run_fuzz --ablation wo_exc --heuristic SA --max_round 3000

# fuzzing tensorflow with SA and two server model
# python fuel/fuzz.py --lib tensorflow run_fuzz --heuristic SA
