import torch

def record_exception(exception, version, filename, err_file, total_errs_file):
    exception = str(exception)
    if "from user code:" in exception:
        exception = exception.split("from user code:")[0]


    with open(err_file, "a+", encoding="utf-8") as f:
        f.write(f"The exception in {version} mode is \n{exception}\n")

    with open(total_errs_file, "a+", encoding="utf-8") as f:
        f.write(
            f"---------------Current test case is {filename} ---------------\n"
            f"The {version} mode has bug, it follows up:\n{exception}\n"
        )



def torch_save(res, res_file):
    if res is None:
        res = torch.Tensor([0])
    if not torch.is_tensor(res):
        try:
            torch.tensor(res)
        except Exception:
            res = torch.tensor([0])
    res = res.to(torch.float32) if res.dtype == torch.bool else res
    torch.save(res, res_file)
