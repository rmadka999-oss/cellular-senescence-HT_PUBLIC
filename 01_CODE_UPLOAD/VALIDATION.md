# Inference-only verification

The new example/model archives were extracted into a separate workspace. Only the inference-only files were used.

- 176 unique supplied model-ready AIF arrays, five fixed scoring artifacts.
- 20 representative examples: maximum score difference 3.94525953018e-07 versus archived expected values.
- 168 nuclear fields: maximum score difference 5.643419521e-07.
- 275 nuclei: all per-field areas match expected values.
- Pooled/within-passage Spearman coefficients and P values match references.
- Passage area means and SEMs match references.
- All full-example checks passed on GPU, FP32, PyTorch 2.7.1+cu118.
- One real AIF was also checked on CPU through all five artifacts; maximum score difference 4.44017116918e-06. Full-cohort CPU timing was not measured.

Reference tolerances are 1e-4 for scores, 1e-8 square micrometres for area/mean/SEM, 1e-12 absolute for rho, and 1e-10 relative for P values. Fixed inputs are supplied; input generation and final-mask segmentation/registration are outside this verification. This is numerical reproduction, not evidence that masks are biological ground truth.
