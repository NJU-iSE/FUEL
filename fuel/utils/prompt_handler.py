import re
from loguru import logger

from ..feedback.feedback import FeedBack


class PromptHandler:
    """Utility class for handling generation and analysis prompts"""
    
    def __init__(self, gen_prompt_config, als_prompt_config):
        self.gen_prompt_config = gen_prompt_config
        self.als_prompt_config = als_prompt_config
    
    def get_prompts(self, feedback_data, lib, op_nums, heuristic=None):
        """Generate appropriate prompts based on current state"""
        statue = feedback_data.get('statue', True)
        _feedback = feedback_data.get('feedback', {})
        
        # Determine whether to use default prompt
        if (
            (FeedBack.success_times < 2 and statue)
            or FeedBack.cons_fail > 2
            or FeedBack.fix_failed
        ):
            FeedBack.cons_fail = 0
            gen_prompt = self.gen_prompt_config["default"]
            als_text = "use generation by default"
            return gen_prompt, als_text
        
        # Select prompts based on success/failure status
        if statue:
            als_prompt = self.als_prompt_config["success"]["coverage"]
            als_prompt = re.sub(r"\{coverage}", _feedback["coverage"], als_prompt)
            gen_prompt = self.gen_prompt_config["success"]
        else:
            FeedBack.cons_fail += 1
            try:
                als_prompt = self.als_prompt_config["failure"]["exception"]
            except KeyError:
                als_prompt = self.als_prompt_config["failure"]
            als_prompt = re.sub(r"\{exception}", _feedback["exception"], als_prompt)
            gen_prompt = self.gen_prompt_config["failure"]
        
        # Process common prompt replacements
        als_prompt = re.sub(r"\{code}", _feedback["code"], als_prompt)
        gen_prompt = re.sub(r"\{code}", _feedback["code"], gen_prompt)
        
        return gen_prompt, als_prompt
    
    def process_generation_prompt(self, gen_prompt, als_text, op_nums, heuristic=None):
        """Process final replacements for generation prompt"""
        gen_prompt = re.sub(
            r"\{als_res}", re.escape(als_text).replace("\\", ""), gen_prompt
        )
        gen_prompt = re.sub(r"\{op_nums}", str(op_nums), gen_prompt)
        
        # Process heuristic algorithm related replacements
        if heuristic != "None" and heuristic is not None:
            if FeedBack.new_ops == []:
                new_ops = heuristic.get_ops()
                FeedBack.cur_ops = new_ops
                FeedBack.delta_lines = 0
            gen_prompt = re.sub(r"\{new_ops}", "\n".join(FeedBack.cur_ops), gen_prompt)
            logger.info(f"current op(s) is/are {FeedBack.cur_ops}")
        
        return gen_prompt 