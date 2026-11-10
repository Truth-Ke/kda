# Adaptation: triton-kernels

Source: https://github.com/huggingface/kernels at `32b3dc8cea813b011885fa656121fe8d9c8415ea`. License: Apache-2.0.

Contiguous is not a hard constraint when the contract includes strides. Do not silently call .contiguous(). Frontmatter converted to YAML. ../rocm-kernels and ../xpu-kernels links rewritten to upstream URLs.

The upstream method is preserved. Only paths, invocation, and contract-precedence notes are adapted.
