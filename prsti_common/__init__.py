"""evidence_extractor와 scoring_engine이 공유하는 코드.

두 컴포넌트 모두 같은 rubric.yaml 구조(items/areas)를 읽어야 하므로, 한쪽
패키지에 종속시키지 않고 이 공유 모듈에 둔다.
"""
