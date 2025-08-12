#!/bin/bash
# unset proxy settings (specified settings for deepseek)
unset http_proxy
unset https_proxy
unset all_proxy
unset HTTP_PROXY 
unset HTTPS_PROXY
unset ALL_PROXY

# fuzzing pytorch with FASA and two server model
python -m fuel.fuzz \
--lib pytorch \
--als_model_config config/model/kimi.yaml \
--als_prompt_config config/als_prompt \
--gen_model_config config/model/kimi.yaml \
--gen_prompt_config config/gen_prompt \
run_fuzz \
--heuristic FASA \
--diff_type cpu_compiler \
--max_round 1000 \


# ablations

# fuzzing pytorch without heuristic
# python fuel/fuzz.py --lib pytorch run_fuzz --heuristic None
# fuzzing pytorch without als
# python fuel/ablation_fuzz.py --lib pytorch --gen_prompt_config config/ablations/wo_als/gen_prompt run_fuzz --ablation wo_als --heuristic FASA --max_round 3000

# fuzzing pytorch without coverage
#python fuel/ablation_fuzz.py --lib pytorch --gen_prompt_config config/ablations/wo_coverage/gen_prompt run_fuzz --ablation wo_cov --heuristic FASA --max_round 3000

# fuzzing pytorch without exception
# python fuel/ablation_fuzz.py --lib pytorch --gen_prompt_config config/ablations/wo_exception/gen_prompt run_fuzz --ablation wo_exc --heuristic FASA --max_round 3000

# fuzzing tensorflow with FASA and two server model
# python fuel/fuzz.py --lib tensorflow run_fuzz --heuristic FASA
