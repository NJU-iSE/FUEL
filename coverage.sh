#!/bin/bash
# shell script to collect code coverage for fuel
python -m experiments.collect_code_coverage --tech fuel --lib pytorch --folder results/fuel/pytorch
