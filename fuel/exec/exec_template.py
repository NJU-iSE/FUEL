from loguru import logger

from ..difftesting.difftesting import DiffTesting
from ..difftesting.oracle import OracleType
from ..exec.render_code import get_rendered_code
from ..exec.utils import is_equal_tensor
from ..feedback.feedback import FeedBack
from ..utils.Filer import File
from ..utils.util import extract_model_code


def exec_template(
    code,
) -> str:  # TODO@SHAOYU: Add support for diff testing on different devices
    # Before execution, the code is unknown.
    FeedBack.feedback_code = OracleType.UNKNOWN
    FeedBack.has_bug = FeedBack.has_exception = False
    try:
        File.rendered_code = get_rendered_code(FeedBack.lib, code)
        if FeedBack.lib == "triton":
            extracted_model_code = File.rendered_code
        else:
            extracted_model_code = extract_model_code(File.rendered_code)
    except Exception as e:
        exception = str(e)
        # situation1: If there is a syntax error in the code, it is deemed an invalid model.
        File.write_file(
            File.err_file,
            f"The code is invalid.The detail is as follows:\n"
            f"\tIt contains syntax error:{exception}",
        )
        File.write_file(
            File.total_errs_file,
            f"---------------Current test case is {File.cur_filename}---------------\n{exception}",
            "a+",
        )
        logger.error("<--------------- Syntax error in the code. --------------->")
        FeedBack.feedback_code = OracleType.SYNTAX_ERROR
        File.write_file(File.fail_file, File.cur_filename)
        return code

    File.write_file(File.tmp_py, File.rendered_code, "w")
    base_code, target_code = DiffTesting.testing()

    File.close_file(File.validate_file)
    File.write_file(
        File.validate_file,
        f"<-- base_code:{base_code}; target_code:{target_code} -->",
    )

    res_base, res_target, max_diff = None, None, None

    if base_code == OracleType.BASE_SUCCESS:
        if target_code == OracleType.TRANSFER_EXCEPTION:
            final_code = OracleType.TRANSFER_EXCEPTION
            File.write_file(
                File.validate_file,
                f"<-- WARNING: {FeedBack.base_version}:SUCCESS, {FeedBack.target_version}:TRANSFER_ERROR  -->",
            )

        elif target_code == OracleType.TARGET_EXCEPTION:
            final_code = OracleType.TARGET_EXCEPTION
            File.write_file(
                File.validate_file,
                f"<-- WARNING: {FeedBack.base_version}:SUCCESS, {FeedBack.target_version}:ERROR  -->",
            )

        elif target_code == OracleType.TARGET_SUCCESS:
            if FeedBack.lib != "tensorflow":
                res_base, res_target = FeedBack.get_validate_result()
                flag, max_diff = is_equal_tensor(FeedBack.lib, res_base, res_target)
                if flag:
                    File.write_file(
                        File.validate_file,
                        "<-- The results of different backend are the same. -->",
                    )
                    final_code = OracleType.TARGET_SUCCESS
                else:
                    File.write_file(
                        File.validate_file,
                        f"<-- WARNING:The results of different backend are different. -->\nDetail follows up:\nThe max diff is {max_diff}\n",
                    )
                    final_code = OracleType.INCON
            else:
                final_code = OracleType.TARGET_SUCCESS
        else:
            final_code = OracleType.SIGKILL

    elif base_code == OracleType.BASE_EXCEPTION:
        FeedBack.has_exception = True
        if target_code == OracleType.TRANSFER_EXCEPTION:
            final_code = OracleType.BASE_EXCEPTION

        elif target_code == OracleType.TARGET_EXCEPTION:
            final_code = OracleType.BASE_EXCEPTION

        elif target_code == OracleType.TARGET_SUCCESS:
            File.write_file(
                File.validate_file,
                f"<-- WARNING: {FeedBack.base_version}:ERROR, {FeedBack.target_version}:SUCCESS  -->",
            )
            final_code = OracleType.MISALIGN

        else:
            final_code = OracleType.SIGKILL

    else:
        final_code = OracleType.SIGKILL

    match final_code:
        case OracleType.SIGKILL:
            File.write_file(
                File.skip_file, f"Round {FeedBack.cur_round}:{File.cur_filename}"
            )
            File.write_file(
                File.err_file, "Process of the code is killed by the system."
            )

        case OracleType.TARGET_SUCCESS:
            File.write_file(
                File.success_file, f"Round {FeedBack.cur_round}:{File.cur_filename}"
            )

        case (
            OracleType.INCON
            | OracleType.TRANSFER_EXCEPTION
            | OracleType.TARGET_EXCEPTION
            | OracleType.MISALIGN
        ):
            File.write_file(
                File.bug_file, f"Round {FeedBack.cur_round}:{File.cur_filename}"
            )
            FeedBack.has_bug = True

        case OracleType.BASE_EXCEPTION:
            File.write_file(
                File.fail_file, f"Round {FeedBack.cur_round}:{File.cur_filename}"
            )

    FeedBack.feedback_code = final_code  # get the execution state

    # Exception error file init
    if FeedBack.feedback_code in (
        OracleType.INCON,
        OracleType.TRANSFER_EXCEPTION,
        OracleType.TARGET_EXCEPTION,
        OracleType.MISALIGN,
    ):
        File.write_file(
            File.bug_report,
            f"<-------------------------- Current filename is {File.cur_filename} -------------------------->",
        )
        File.write_file(
            File.bug_report,
            f"\n<-- DIFF_TYPE:{DiffTesting.diff_type} -->\n",
        )
        File.write_file(
            File.bug_report,
            f"Code follows up:\n{File.rendered_code}\nmodel(*inputs)\n# print(model(*inputs))\n",
        )
    exception = File.read_file(File.err_file)

    # situation1: exception occurs in both base and target mode -> invalid model
    if "base" in exception and "target" in exception:
        File.write_file(
            File.err_file,
            f"The code is invalid\n"
            f"The code throws exceptions during execution in both {FeedBack.base_version} mode and {FeedBack.target_version} mode.\n"
            f"{exception}",
            "w",
        )

    if FeedBack.feedback_code == OracleType.INCON:
        File.write_file(
            File.bug_report,
            f"\n--------------【The results of different backend are different.】--------------\n\nDetail follows up:\nThe max diff is {max_diff}\n",
        )

        # situation3：Numerical inconsistency.
        File.write_file(
            File.err_file,
            f"\nThe results of model execution on {FeedBack.base_version} and {FeedBack.target_version} produced numerical inconsistencies.\n"
            f"\tThe maximum difference between the corresponding elements of different output tensors is {max_diff}\n",
            "w",
        )

    elif FeedBack.feedback_code == OracleType.TRANSFER_EXCEPTION:
        File.write_file(
            File.bug_report,
            f"--------------【The code executes successfully in {FeedBack.base_version} mode but fails while preparing {FeedBack.target_version} mode.】--------------\n",
        )

        File.write_file(
            File.err_file,
            f"The code throws an exception during execution.\n"
            f"\tThe code executes successfully in {FeedBack.base_version} mode but fails while preparing {FeedBack.target_version} mode.\n"
            f"\t\t{exception}",
            "w",
        )

    elif FeedBack.feedback_code == OracleType.TARGET_EXCEPTION:
        File.write_file(
            File.bug_report,
            f"--------------【The code executes successfully in {FeedBack.base_version} mode but fails in {FeedBack.target_version} mode.】--------------\n",
        )

        # situation2:An exception occurs in a single backend.
        File.write_file(
            File.err_file,
            f"The code throws an exception during execution.\n"
            f"\tThe code executes successfully in {FeedBack.base_version} mode but fails in {FeedBack.target_version} mode.\n"
            f"\t\t{exception}",
            "w",
        )

    elif FeedBack.feedback_code == OracleType.MISALIGN:
        File.write_file(
            File.bug_report,
            f"--------------【The code fails in {FeedBack.base_version} mode but executes successfully in {FeedBack.target_version} mode.】--------------\n",
        )

        # situation2:An exception occurs in a single backend.
        File.write_file(
            File.err_file,
            f"The code throws an exception during execution.\n"
            f"\tThe code fails in {FeedBack.base_version} mode but executes successfully in {FeedBack.target_version} mode.\n"
            f"\t\t{exception}",
            "w",
        )
    return extracted_model_code
