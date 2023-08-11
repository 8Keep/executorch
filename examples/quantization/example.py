# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import copy

import torch._export as export
from torch.ao.quantization.quantize_pt2e import convert_pt2e, prepare_pt2e
from torch.ao.quantization.quantizer import XNNPACKQuantizer
from torch.ao.quantization.quantizer.xnnpack_quantizer import (
    get_symmetric_quantization_config,
)

# TODO: maybe move this to examples/export/utils.py?
# from ..export.export_example import export_to_ff

from ..models import MODEL_NAME_TO_MODEL


def quantize(model_name, model, example_inputs):
    m = model.eval()
    m = export.capture_pre_autograd_graph(m, copy.deepcopy(example_inputs))
    print("original model:", m)
    quantizer = XNNPACKQuantizer()
    # if we set is_per_channel to True, we also need to add out_variant of quantize_per_channel/dequantize_per_channel
    operator_config = get_symmetric_quantization_config(is_per_channel=False)
    quantizer.set_global(operator_config)
    m = prepare_pt2e(m, quantizer)
    # calibration
    m(*example_inputs)
    m = convert_pt2e(m)
    print("quantized model:", m)
    # make sure we can export to flat buffer
    # Note: this is not working yet due to missing out variant ops for quantize_per_tensor/dequantize_per_tensor ops
    # aten = export_to_ff(model_name, m, copy.deepcopy(example_inputs))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--model_name",
        required=True,
        help=f"Provide model name. Valid ones: {list(MODEL_NAME_TO_MODEL.keys())}",
    )

    args = parser.parse_args()

    if args.model_name not in MODEL_NAME_TO_MODEL:
        raise RuntimeError(
            f"Model {args.model_name} is not a valid name. "
            f"Available models are {list(MODEL_NAME_TO_MODEL.keys())}."
        )

    model, example_inputs = MODEL_NAME_TO_MODEL[args.model_name]()

    quantize(args.model_name, model, example_inputs)
