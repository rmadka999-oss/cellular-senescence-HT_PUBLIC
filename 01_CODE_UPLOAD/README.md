# Senescence score inference and final-mask nuclear analysis

This package performs two operations: scoring the supplied model-ready AIF examples with fixed inference artifacts, and computing nuclear areas/associations from supplied final label masks.

## Supplied inputs

- 20 representative AIF examples at P2/P4/P17/P27.
- 168 nuclear-validation fields, with275 nuclei in final label masks.
- 176 unique AIF arrays because 12 fields are shared by the two sets.
- AIF files are **model-ready 2D float32 arrays in [0,1]**, not physical-RI arrays or original HT volumes. Use them directly. Do not add normalization, cropping or intensity adjustments.
- Five fixed scoring artifacts. The example manifest specifies which artifacts to average for each internal-validation example. For these examples, do not indiscriminately average every artifact.

## Install

Python 3.9 was used for verification. Create a separate environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install numpy==2.0.2 scipy==1.13.1
python -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cpu
```

For GPU execution, use a PyTorch build compatible with your CUDA environment instead of the CPU build.

## Run

When using the full local delivery, keep 01_CODE_UPLOAD beside 02_RELEASE_UPLOAD and run inside 01_CODE_UPLOAD:

```bash
python run_demo.py --device cpu
```

For a configured GPU: `python run_demo.py --device cuda:0`.
`--scope montage` runs the 20 representative images; `--scope nuclear` runs the 168-field nuclear analysis; the default runs both.

If cloned from a public repository, the runner can download the two assets from its v2.0.0 Release using the git remote. Without git metadata, supply `--repository OWNER/REPO`, or place both ZIPs in a directory and use `--assets-dir /path/to/assets`.

The downloaded assets are checked against config/assets.json. Each artifact and final mask is also checked by hash. No credentials or laboratory file paths are needed. With assets already available locally, computation does not need Internet access.

## Outputs and checks

Outputs include montage/nuclear field scores with expected values and numerical errors, per-nucleus areas, per-field mean nuclear areas, passage mean/SEM, pooled/within-passage Spearman associations and verification.json. The script exits with a failed status if reference checks fail. The score tolerance is 1e-4; nuclear areas/means/SEMs use absolute tolerance 1e-8 square micrometres; correlation checks use rho absolute tolerance 1e-12 andP relative tolerance 1e-10.

Nuclear area is label pixel count times the two fluorescence pixel spacings. All supplied positive labels, including border-touching labels, are retained, and nuclear areas are averaged within each field. Spearman correlations are two-sided; OLS coefficients are descriptive. Fields are technical observations, not independent culture replicates. Masks are provided as analytical inputs, not asserted biological ground truth.

## Public scope

This code accepts only supplied model-ready AIF arrays and final masks. It does not reconstructHT, generate AIF, segment new fluorescence, register images or estimate new scoring parameters. The scalar score is obtained from a fixed encoder and fixed linear readout. No parameter-estimation procedure or construction configuration is distributed. The20 selected examples do not reproduce a full-population validation accuracy.

See VALIDATION.md for measured reproduction checks and NOTICE for rights information.
