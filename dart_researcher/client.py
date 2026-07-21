"""DART Open API 클라이언트. requests만 쓰는 얇은 래퍼.

인증키는 DART_API_KEY 환경변수에서만 읽는다 — 코드나 커밋에 절대 남기지 않는다.
"""

from __future__ import annotations

import io
import os
import re
import zipfile
from dataclasses import dataclass

import requests

BASE_URL = "https://opendart.fss.or.kr/api"


class MissingAPIKeyError(RuntimeError):
    """DART_API_KEY 환경변수가 없을 때."""


class DartApiError(RuntimeError):
    """DART API가 status != '000'(정상)을 반환했을 때, 또는 응답을 해석할 수 없을 때."""


def _get_api_key() -> str:
    key = os.environ.get("DART_API_KEY")
    if not key:
        raise MissingAPIKeyError(
            "DART_API_KEY 환경변수가 설정되어 있지 않습니다. "
            "https://opendart.fss.or.kr 에서 발급받아 사용자 본인 계정으로 환경변수를 설정하세요."
        )
    return key


@dataclass(frozen=True)
class DisclosureListItem:
    corp_code: str
    corp_name: str
    stock_code: str
    report_nm: str
    rcept_no: str
    flr_nm: str
    rcept_dt: str
    rm: str


class DartClient:
    """DART_API_KEY가 없으면 생성 시점에 즉시 실패한다 — 호출 도중이 아니라."""

    def __init__(self, session: requests.Session | None = None):
        self._api_key = _get_api_key()
        self._session = session or requests.Session()
        self._corp_code_cache: list[dict] | None = None

    def _get(self, path: str, **params) -> requests.Response:
        query = {"crtfc_key": self._api_key, **params}
        response = self._session.get(f"{BASE_URL}/{path}", params=query, timeout=30)
        response.raise_for_status()
        return response

    def find_corp_code(self, company_name: str) -> str:
        """corpCode.xml(전체 상장사 코드 목록, ZIP)에서 회사명으로 corp_code를 찾는다.

        이 목록을 한 번 내려받는 것은 '대량 수집'이 아니다 — DART가 corp_code를 얻는
        유일한 공식 방법이며, 개별 기업 공시를 순회 조회하는 것과는 다르다.
        """
        codes = self._load_corp_codes()
        matches = [c for c in codes if c["corp_name"] == company_name]
        if not matches:
            raise DartApiError(f"'{company_name}'에 해당하는 corp_code를 찾지 못했습니다.")
        if len(matches) > 1:
            listed = [m for m in matches if m["stock_code"].strip()]
            if len(listed) == 1:
                return listed[0]["corp_code"]
            raise DartApiError(f"'{company_name}'에 해당하는 corp_code가 여러 개입니다: {matches}")
        return matches[0]["corp_code"]

    def _load_corp_codes(self) -> list[dict]:
        if self._corp_code_cache is not None:
            return self._corp_code_cache
        response = self._get("corpCode.xml")
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            xml_bytes = zf.read(zf.namelist()[0])
        text = xml_bytes.decode("utf-8", errors="replace")
        codes = [
            {"corp_code": m.group(1), "corp_name": m.group(2), "stock_code": m.group(3)}
            for m in re.finditer(
                r"<list>.*?<corp_code>(.*?)</corp_code>.*?<corp_name>(.*?)</corp_name>.*?"
                r"<stock_code>(.*?)</stock_code>.*?</list>",
                text,
                re.DOTALL,
            )
        ]
        self._corp_code_cache = codes
        return codes

    def list_disclosures(
        self, corp_code: str, bgn_de: str, end_de: str, pblntf_ty: str | None = None
    ) -> list[DisclosureListItem]:
        """공시검색(list.json). 특정 corp_code + 기간으로만 조회한다(전체 상장사 순회 아님)."""
        params: dict = {"corp_code": corp_code, "bgn_de": bgn_de, "end_de": end_de, "page_count": 100}
        if pblntf_ty:
            params["pblntf_ty"] = pblntf_ty
        data = self._get("list.json", **params).json()
        if data.get("status") == "013":  # 조회된 데이터가 없습니다
            return []
        if data.get("status") != "000":
            raise DartApiError(f"DART API 오류: {data.get('status')} {data.get('message')}")
        return [
            DisclosureListItem(
                corp_code=item["corp_code"],
                corp_name=item["corp_name"],
                stock_code=item.get("stock_code", ""),
                report_nm=item["report_nm"],
                rcept_no=item["rcept_no"],
                flr_nm=item["flr_nm"],
                rcept_dt=item["rcept_dt"],
                rm=item.get("rm", ""),
            )
            for item in data.get("list", [])
        ]

    def fetch_document_text(self, rcept_no: str) -> str:
        """document.xml(공시서류원본, ZIP)을 내려받아 태그를 제거한 평문으로 반환한다.

        DART 고유 XML 구조(SECTION/TABLE 등)를 완전히 파싱하지 않고 태그만 벗겨낸다 —
        표·문단 구조 정보는 잃지만 키워드 위치 탐색에는 평문으로 충분하고, 원문 자체는
        보존된다(요약하지 않는다).
        """
        response = self._get("document.xml", rcept_no=rcept_no)
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            raw = b"".join(zf.read(name) for name in zf.namelist())
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("euc-kr", errors="replace")
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&[a-zA-Z0-9#]+;", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
