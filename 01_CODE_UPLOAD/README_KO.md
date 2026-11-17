# AIF 점수 추론과 최종 핵 마스크 분석

이 공개용 코드는 두 작업만 수행합니다.

1. 제공된 **모델 입력용 AIF**에서 고정 모델로 노화점수를 계산합니다.
2. 제공된 **최종 핵 마스크**로 핵 면적과 점수의 상관관계를 계산합니다.

## 입력 자료

대표 AIF 20장과 핵 검증 168 FOV의 AIF·최종 마스크(핵 275개)를 제공합니다. 중복 12장을 제외한 AIF는 176장입니다.

AIF는 **0–1 범위의 모델 입력용 2D float32 배열**입니다. 물리 RI 값 자체나 원본 HT가 아닙니다. 추가 정규화·자르기·밝기 조정을 하지 않고 그대로 사용합니다. 파일에는 원본 촬영 경로나 생성 설정이 들어 있지 않습니다.

예제별 CSV의 models 열에 지정된 모델들만 평균합니다. 예제는 내부 검증 자료이므로 모든 예제에 모델 5개를 무조건 평균하는 방식은 사용하지 않습니다.

## 설치와 실행

Python 3.9 환경에서 검증했습니다. 01_CODE_UPLOAD 안에서 실행합니다.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install numpy==2.0.2 scipy==1.13.1
python -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cpu
python run_demo.py --device cpu
```

전체 폴더를 받았다면 옆의 02_RELEASE_UPLOAD에서 ZIP을 자동으로 찾습니다. GPU용 PyTorch를 설치했다면 --device cuda:0을 사용할 수 있습니다.

- 대표 20장만: `--scope montage`
- 핵 검증만: `--scope nuclear`
- 기본: 둘 다 실행

공개 저장소에서 clone한 경우 v2.0.0 Release에서 자료를 받을 수 있습니다. git 정보 없이 코드만 받았다면 `--repository 소유자/저장소` 또는 `--assets-dir ZIP폴더`를 지정합니다.

## 핵 분석과 재현 확인

점수는 실제 AIF로 다시 계산합니다. 최종 라벨 마스크의 픽셀 수에 형광 픽셀 간격을 곱해 핵 면적을 구하고 FOV 안에서 평균합니다. 제공된 경계 핵도 포함합니다. 계대별 평균·SEM, 전체·계대별 Spearman 계수와 P값을 비교합니다.

핵 마스크를 새로 생성하거나 정합을 다시 하는 기능은 포함하지 않습니다. 코드에는 입력 생성·매개변수 추정 기능이 없으며, 제공된 고정 입력과 추론 계수만 사용합니다. 검사 결과는 verification.json에 저장됩니다.
