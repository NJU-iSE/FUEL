import os
import time

from loguru import logger

from ..difftesting.difftesting import DiffTesting
from ..difftesting.oracle import OracleType
from ..exec.exec_template import exec_template
from ..feedback.feedback import FeedBack
from ..utils.Filer import File
from ..utils.util import extra_code_from_text


class FuzzingCore:
    """Core fuzzing test logic"""

    def __init__(self, gen_model, als_model, prompt_handler, lib):
        self.gen_model = gen_model
        self.als_model = als_model
        self.prompt_handler = prompt_handler
        self.lib = lib
        self.st_time = time.time()

    def execute_single_round(self, feedback_data, heuristic, op_nums, diff_type):
        """Execute single round of fuzzing test"""
        logger.success(f"-------Current Round:{FeedBack.cur_round}-------")
        logger.success("[gen starts!]")

        filename = os.path.join(File.res_dir, f"{int(time.time() - self.st_time)}.py")

        # Get prompts
        gen_prompt, als_prompt_or_text = self.prompt_handler.get_prompts(
            feedback_data, self.lib, op_nums, heuristic
        )

        # If analysis is needed
        if (
            isinstance(als_prompt_or_text, str)
            and als_prompt_or_text != "use generation by default"
        ):
            als_text = self.als_model.analyze(
                role=self.prompt_handler.als_prompt_config["system_content"].format(
                    lib=self.lib
                ),
                prompt=als_prompt_or_text,
            )
        else:
            als_text = als_prompt_or_text

        # Process generation prompt
        gen_prompt = self.prompt_handler.process_generation_prompt(
            gen_prompt, als_text, op_nums, heuristic
        )

        # Write logs
        File.write_file(
            File.gen_file,
            f"----current round is {FeedBack.cur_round}----\n{gen_prompt.split('### Results')[-1]}",
        )

        # Generate code
        gen_text = self.gen_model.generate(
            role=self.prompt_handler.gen_prompt_config["system_content"].format(
                lib=self.lib
            ),
            prompt=gen_prompt,
        )

        # Write analysis logs
        File.write_file(
            File.als_file,
            f"""-------------Current analysis file is {File.cur_filename} -------------
                                                              \rCode follows up: \n{File.eliminated_code}
                                                              \rAnalysis text follows up:\n{als_text}
                                                              \n""",
        )

        # Extract and execute code
        file_path, code = filename, extra_code_from_text(gen_text)
        File.cur_filename = file_path
        logger.success("[gen finshes!]")

        # Execute differential testing
        DiffTesting.diff_type = diff_type
        exec_template(code)

        return file_path

    def handle_execution_results(self, file_path, flag):
        """Handle execution results and fix logic"""
        FeedBack.fix_failed = False
        FeedBack.new_ops = []

        if FeedBack.has_bug:
            if flag:
                FeedBack.fix_total_times += 1
                File.write_file(
                    File.fix_file,
                    f"<------ No.{FeedBack.fix_total_times}:{File.cur_filename} ------>",
                )
                flag = False
                FeedBack.new_ops = FeedBack.cur_ops
            else:
                # Fix successful
                File.write_file(
                    File.fix_file, f"| Fix Successfully:{File.cur_filename}"
                )
                FeedBack.fix_success_times += 1
                flag = True

        elif FeedBack.has_exception:
            if flag:
                FeedBack.fix_total_times += 1
                File.write_file(
                    File.fix_file,
                    f"<------ No.{FeedBack.fix_total_times}:{File.cur_filename} ------>",
                )
                flag = False
                FeedBack.new_ops = FeedBack.cur_ops
            else:
                # Fix failed
                File.write_file(File.fix_file, f"| Fix Failed:{File.cur_filename}")
                FeedBack.fix_fail_times += 1
                FeedBack.fix_failed = True
                flag = True
        else:
            if not flag:
                # Fix successful
                File.write_file(
                    File.fix_file, f"| Fix Successfully:{File.cur_filename}"
                )
                FeedBack.fix_success_times += 1
                flag = True

        return flag

    def process_feedback(self, file_path):
        """Process feedback and coverage"""
        logger.info(f"<-- After exec, current filename is: {file_path} -->")
        File.write_file(file_path, File.eliminated_code)

        # Get exception status
        statue, exception = FeedBack.get_exception()

        feedback_data = {}
        if statue:
            # Calculate coverage
            FeedBack.cal_coverage()
            cov_flag, feedbk = FeedBack.get_delta_coverage()

            if not cov_flag:
                FeedBack.feedback_code = OracleType.SUCCESS_WITHOUT_NEWCOV
            else:
                FeedBack.feedback_code = OracleType.SUCCESS_WITH_NEWCOV

            feedback_data = {
                "code": File.eliminated_code,
                "coverage": feedbk,
            }

            File.write_file(
                File.validate_file,
                f"<-- Current coverage rate is {FeedBack.cur_lines / FeedBack.whole_lines:.4%};"
                f"Total coverage rate is {FeedBack.total_lines / FeedBack.whole_lines:.4%} -->",
            )

            if FeedBack.success_times == 0:
                feedbk = "First Succeeded round don't record!"

            File.write_file(
                File.feedback_file,
                f"----Current round is {FeedBack.cur_round}----\n"
                f"Current file is {File.cur_filename}\n"
                f"{feedbk}\n",
            )

            FeedBack.success_times += 1
            if FeedBack.success_times >= 2:
                logger.success("execute successfully\n")
                # logger.debug(f"The feedback follows up: \n{feedbk}\n")
        else:
            feedbk = exception
            feedback_data = {
                "code": File.eliminated_code,
                "exception": feedbk,
            }

            File.write_file(
                File.feedback_file,
                f"----Current round is {FeedBack.cur_round}----\n"
                f"Current file is {File.cur_filename}\n"
                f"{feedbk}\n",
            )

            if FeedBack.success_times >= 2:
                logger.success("execute successfully\n")
                # logger.exception(f"The feedback follows up: \n{feedbk}\n")

        # logger.debug(f"The code follows up: \n\n{File.eliminated_code}\n")
        logger.info(
            f"fix total: {FeedBack.fix_success_times + FeedBack.fix_fail_times},success:{FeedBack.fix_success_times}\n"
        )
        logger.success("[Current Round Is Successful!]\n")

        return {"statue": statue, "feedback": feedback_data}
