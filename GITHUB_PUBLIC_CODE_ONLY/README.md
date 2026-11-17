# Senescence inference and final-mask analysis

This repository provides code for scoring separately supplied model-ready AIF inputs and for computing nuclear areas/associations from separately supplied final masks.

**Twenty representative AIF images are provided for visual inspection (see below). Nuclear masks, model weights, fixed score coefficients, actual model manifests and study configuration files are not distributed. No automatic download is implemented in the analysis programs. This repository alone is not a self-contained score-reproduction package; the remaining required materials must be obtained separately.**

## Public example AIF images

Twenty representative AIF images from the previous v1.1.0 distribution are
available: five each for P2, P4, P17 and P27. Each archive contains the
unchanged original float32 NPY AIF arrays and PNG previews for visual inspection.

| Passage | Images | Download |
|---|---:|---|
| P2 | 5 | [AIF20_P2.zip](../data/AIF20_P2.zip?raw=true) |
| P4 | 5 | [AIF20_P4.zip](../data/AIF20_P4.zip?raw=true) |
| P17 | 5 | [AIF20_P17.zip](../data/AIF20_P17.zip?raw=true) |
| P27 | 5 | [AIF20_P27.zip](../data/AIF20_P27.zip?raw=true) |

[View all 20 images](../data/AIF20_CONTACT_SHEET.png) ·
[Individual PNG previews](../data/preview/) ·
[Image index](../data/AIF20_INDEX.csv) ·
[Archive checksums](../data/SHA256SUMS.txt)

These original arrays contain physical refractive-index values. They are not
the separately supplied 0–1 model-ready input arrays required by `score_aif.py`.
The PNGs are display previews, not numerical scoring inputs. The public images
allow visual inspection; images and code alone do not reproduce scores without
the separately supplied model-ready inputs, model artifacts and fixed parameters.
No image-conversion recipe or its detailed settings are distributed here.
The example images are not covered by the code license below.

## Installation

Python 3.9 was used for verification. In a separate environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install numpy==2.0.2 scipy==1.13.1
python -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cpu
```

For GPU execution, install a compatible CUDA build instead of the CPU build. Dependency installation may use Internet access; the analysis programs only read local files.

## Score local AIF inputs

```bash
python score_aif.py \
  --manifest /path/to/private_materials/input_manifest.csv \
  --data-dir /path/to/private_materials/examples \
  --model-manifest /path/to/private_materials/models.json \
  --models-dir /path/to/private_materials/models \
  --output /path/to/new_score_results \
  --device cpu
```

All paths above are placeholders. Output directories must not already exist.

The input CSV needs `sample_id`, `path` and `models` columns. IDs must be unique. AIF paths are relative to data-dir. The models column contains applicable IDs separated by semicolons. Use the model subset specified in the separately provided materials rather than assuming every model applies to every internal-validation example. Optional columns include passage and expected_score. If expected scores are provided, the program checks a numerical tolerance of 1e-4.

The local model JSON is a list of objects with id, file and sha256 fields. Actual values and corresponding inference artifacts are not distributed here. Inputs must be supplied model-ready 2D float32 AIF arrays in [0,1]. The interface does not accept original HT volumes or unconverted physical-RI inputs.

The program writes scores.csv, scores_per_model.csv, scored_manifest.csv and verification.json. The scored manifest preserves local input metadata and adds the newly calculated score so final-mask analysis can follow.

## Analyze local final masks

```bash
python analyze_masks.py \
  --manifest /path/to/new_score_results/scored_manifest.csv \
  --data-dir /path/to/private_materials/examples \
  --output /path/to/new_nuclear_results
```

The nuclear manifest requires sample_id, passage, score, mask_path, mask_sha256, pixel_size_x_um and pixel_size_y_um. The mask path is relative to data-dir. Optional expected_mean_area_um2 enables an area-reference check.

Final masks are NPZ files containing only a 2D nonnegative integer array named mask; positive labels identify nuclei. Area equals label pixel count times the two fluorescence pixel spacings. Retain supplied border-touching nuclei and average nuclear areas per field. Supply enough varying observations within each passage for association analysis.

Outputs include per-object and per-field areas, passage means/SEMs, pooled/within-passage two-sided Spearman correlations and nominal P values. OLS coefficients are descriptive. FOV observations are not equivalent to independent culture replicates.

## Scope

This repository contains no input-generation, model-development, parameter-estimation, mask-segmentation or registration procedure. It uses only separately supplied fixed inputs and inference artifacts. Numerical reproduction does not establish segmentation ground truth or generalization to new acquisition conditions.

Except for the twenty public example AIF images linked above, material access is determined separately by the researchers. This code does not promise public availability of the remaining materials. See NOTICE for scope information.

## License

The AIF senescence-score inference code in this directory
(score_aif.py, inference.py, and the shared helper common.py)
is licensed under the
[PolyForm Noncommercial License 1.0.0](../LICENSE)
(SPDX: PolyForm-Noncommercial-1.0.0).

This license applies only to the listed code files. It does not
cover the final-mask analysis code, example AIF images or other
research data, model weights, fixed score coefficients, or
third-party dependencies. Third-party dependencies retain
their respective licenses.
