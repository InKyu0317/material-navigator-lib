# material-navigator-lib (mat_nav_lib)

유리·세라믹 소재 연구를 위한 경량 Python 패키지 — 산화물 데이터 및 물성 예측 유틸리티

> LAB Pilot 플랫폼의 소재 데이터 백엔드입니다.  
> 관련 프로젝트: [lab-pilot-demo](https://github.com/InKyu0317/lab-pilot-demo) · [sila-server-manager](https://github.com/InKyu0317/sila-server-manager)

---

## 주요 기능

### 산화물 데이터베이스
- 유리 조성 설계에 사용되는 **70종 산화물** 정적 데이터
- [GlassPy](https://github.com/drcassar/glasspy) GlassNet 원소 목록(68종) 기반으로 매핑
- PyTorch / GlassPy 런타임 의존성 없이 사용 가능 (경량)

### 카테고리 분류

| 카테고리 | 설명 | 예시 |
|----------|------|------|
| `network_former` | 망목형성체 | SiO₂, B₂O₃, P₂O₅, GeO₂ |
| `network_modifier` | 망목수식체 | Na₂O, K₂O, CaO, MgO, BaO |
| `intermediate` | 중간산화물 | Al₂O₃, TiO₂, ZrO₂, ZnO |
| `other` | 전이금속·희토류 등 | MnO, CoO, La₂O₃, CeO₂ |

### 각 산화물 데이터 필드

| 필드 | 타입 | 예시 |
|------|------|------|
| `formula` | str | `"SiO2"` |
| `name_ko` | str | `"이산화규소"` |
| `molar_mass` | float | `60.08` |
| `category` | str | `"network_former"` |

---

## 기술 스택

| 카테고리 | 기술 |
|----------|------|
| 언어 | Python 3.10+ |
| 의존성 | 없음 (순수 Python) |
| 선택 의존성 | `glasspy>=0.6.0` (물성 예측 기능 사용 시) |
| 빌드 | setuptools >= 68.0 |

---

## 프로젝트 구조

```
mat_nav_lib/
├── mat_nav_lib/
│   ├── __init__.py     # get_oxides, get_oxide_formulas, OXIDE_LIST export
│   └── oxides.py       # 70종 산화물 정적 데이터 + 필터 함수
└── pyproject.toml
```

---

## 설치

```bash
# 개발 모드 설치 (소스에서)
pip install -e .

# 또는 직접 경로 지정
PYTHONPATH=/path/to/mat_nav_lib python your_script.py
```

---

## 사용법

```python
from mat_nav_lib import get_oxides, get_oxide_formulas, OXIDE_LIST

# 전체 목록
all_oxides = get_oxides()
print(f"Total: {len(all_oxides)} oxides")

# 카테고리 필터링
formers = get_oxides(category="network_former")
# [{'formula': 'SiO2', 'name_ko': '이산화규소', 'molar_mass': 60.08, 'category': 'network_former'}, ...]

# 수식 리스트만
formulas = get_oxide_formulas()
# ['SiO2', 'B2O3', 'P2O5', ...]
```

---

## FastAPI 연동 예시

```python
from fastapi import APIRouter
from mat_nav_lib import get_oxides

router = APIRouter(prefix="/materials", tags=["materials"])

@router.get("/oxides")
async def list_oxides(category: str | None = None):
    return get_oxides(category=category)
```

---

## 로드맵

- [ ] GlassPy 연동 물성 예측 (`predict` extra)
- [ ] 원료(raw material) → 산화물 변환 유틸리티
- [ ] 배치 계산 (batch calculation) API

---

## 라이선스

MIT
