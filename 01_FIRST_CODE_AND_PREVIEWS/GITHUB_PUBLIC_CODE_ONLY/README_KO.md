# 노화점수 추론 및 최종 핵 마스크 분석

이 저장소에는 다음 코드와 실행 안내, 대표 AIF 20장을 포함합니다.

1. 별도로 제공받은 모델 입력용 AIF에서 고정 모델로 점수 계산.
2. 별도로 제공받은 최종 핵 마스크와 FOV 점수로 핵 면적·상관관계 계산.

**대표 AIF 20장은 열람용으로 공개합니다. 핵 마스크, 가중치, 고정 점수 계수 및 실제 모델 설정 파일은 공개하지 않습니다. 분석 코드의 자동 다운로드 기능도 없습니다. 이 저장소만 받아 즉시 점수를 재계산할 수는 없으며, 나머지 필수 자료는 별도로 제공받아야 합니다.**

## 공개 예제 AIF 영상

이전 v1.1.0 배포에 포함했던 대표 AIF 20장(P2·P4·P17·P27 각 5장)을 제공합니다.
각 ZIP에는 이전 배포와 바이트 단위로 같은 float32 NPY 원본 배열과
열람용 PNG가 들어 있습니다.

| 계대 | 영상 수 | 다운로드 |
|---|---:|---|
| P2 | 5 | [AIF20_P2.zip](../data/AIF20_P2.zip?raw=true) |
| P4 | 5 | [AIF20_P4.zip](../data/AIF20_P4.zip?raw=true) |
| P17 | 5 | [AIF20_P17.zip](../data/AIF20_P17.zip?raw=true) |
| P27 | 5 | [AIF20_P27.zip](../data/AIF20_P27.zip?raw=true) |

[20장 한눈에 보기](../data/AIF20_CONTACT_SHEET.png) ·
[낱장 PNG](../data/preview/) · [영상 목록](../data/AIF20_INDEX.csv) ·
[ZIP 체크섬](../data/SHA256SUMS.txt)

공개 NPY는 물리적 RI 값을 담은 원본 AIF입니다. `score_aif.py`가 요구하는
0–1 범위의 모델 입력 배열과는 다릅니다. PNG는 열람용이며 수치 추론 입력이 아닙니다.
영상과 코드만으로 노화 점수를 재계산할 수는 없으며, 별도로 제공하는 모델 입력,
모델 파일과 고정 매개변수가 필요합니다. 영상 변환 절차와 세부 설정은 공개하지 않습니다.
예제 영상에는 아래 코드 라이선스를 적용하지 않습니다.

## 설치

Python 3.9에서 검사했습니다. 별도 환경에서 의존성을 설치하세요.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install numpy==2.0.2 scipy==1.13.1
python -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cpu
```

GPU를 사용할 경우 해당 환경에 맞는 PyTorch 빌드를 사용합니다. 설치에는 인터넷이 필요할 수 있지만, 분석 코드는 로컬 파일만 읽습니다.

## 1. 제공받은 AIF 점수 계산

```bash
python score_aif.py \
  --manifest /path/to/private_materials/input_manifest.csv \
  --data-dir /path/to/private_materials/examples \
  --model-manifest /path/to/private_materials/models.json \
  --models-dir /path/to/private_materials/models \
  --output /path/to/new_score_results \
  --device cpu
```

위 경로는 예시입니다. 실제로 별도 제공받은 파일 위치를 지정합니다. 출력 폴더는 아직 존재하지 않는 새 경로여야 합니다.

입력 CSV의 필수 열:

| 열 | 의미 |
|---|---|
| sample_id | 중복되지 않는 입력 식별자 |
| path | data-dir에 대한 AIF 상대 경로 |
| models | 해당 입력에 적용할 모델 ID. 여러 개면 세미콜론으로 구분 |

`passage`는 그룹 분석용 선택 열입니다. `expected_score`가 있으면 점수 수치 비교를 수행합니다. 실제 연구 예제를 분석할 때는 별도 제공된 models 값을 그대로 사용합니다.

모델 목록 JSON은 각 모델의 `id`, `file`, `sha256` 필드를 가진 목록입니다. 실제 값과 대응하는 모델 파일은 이 저장소에 포함하지 않습니다. AIF는 모델 입력용으로 준비된 2D float32, 0–1 범위 배열이어야 하며 추가 변환 없이 사용합니다. 원본 HT나 물리 RI 배열을 그대로 넣는 인터페이스는 아닙니다.

출력:

- scores.csv: 입력별 점수와 선택적 기준값 비교.
- scores_per_model.csv: 적용한 모델별 점수.
- scored_manifest.csv: 입력 메타데이터와 새로 계산한 score. 핵 분석에 이어서 사용할 수 있습니다.
- verification.json: 기준값이 제공된 경우의 검사 결과.

## 2. 제공받은 최종 마스크의 핵 면적·상관 분석

```bash
python analyze_masks.py \
  --manifest /path/to/new_score_results/scored_manifest.csv \
  --data-dir /path/to/private_materials/examples \
  --output /path/to/new_nuclear_results
```

핵 분석 CSV에는 `sample_id`, `passage`, `score`, `mask_path`, `mask_sha256`, `pixel_size_x_um`, `pixel_size_y_um` 열이 필요합니다. `mask_path`는 data-dir에 대한 상대 경로입니다. `expected_mean_area_um2`가 있으면 FOV 면적 기준값을 비교합니다.

마스크는 양의 정수 라벨로 핵을 구분한 2D 배열이며, `mask` 배열 하나가 들어 있는 NPZ 형식입니다. 면적은 라벨 픽셀 수에 두 방향의 형광 픽셀 간격을 곱해 구합니다. 제공된 경계 핵도 포함하고, 핵 면적을 FOV 안에서 평균합니다. 그룹별 상관을 계산할 수 있는 수와 변동을 가진 자료가 필요합니다.

출력은 개별 핵 면적, FOV별 평균 면적, 계대별 평균·SEM, 전체 및 계대별 양측 Spearman 상관계수·P값입니다. OLS 계수는 기술적 표시용입니다. FOV는 독립 배양 반복과 동일하지 않으며, P값은 명목값입니다.

## 범위

코드에는 입력 영상 생성, 모델 학습, 새 점수 기준 적합, 핵 마스크 생성, 새 정합 기능이 없습니다. 제공된 입력·고정 추론 파일·최종 마스크의 분석에 한정됩니다. 마스크를 생물학적 정답으로 보증하지 않습니다.

위에서 링크한 대표 AIF 20장 외의 연구 자료와 모델 제공 범위·경로는 연구자가 별도로 정합니다. 이 저장소는 나머지 자료의 공개 제공을 약속하거나 자동으로 요청하지 않습니다. 적용 범위는 NOTICE를 참고하세요.

## 라이선스

이 디렉터리의 AIF 노화 점수 추론 코드인 `score_aif.py`, `inference.py`,
공유 보조 코드 `common.py`에만
[PolyForm Noncommercial License 1.0.0](../LICENSE)을 적용합니다.
SPDX 식별자는 `PolyForm-Noncommercial-1.0.0`입니다.

이 라이선스는 위에 명시한 코드 파일에만 적용되며, 최종 마스크 분석 코드,
예제 AIF 영상이나 기타 연구 데이터, 모델 가중치, 고정 점수 산출 계수,
서드파티 의존성에는 적용되지 않습니다. 서드파티 의존성은 각각의 기존
라이선스를 따릅니다. 제외된 항목에 대해 이 라이선스로 이용 권한을 부여하지 않습니다.
