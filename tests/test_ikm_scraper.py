import json
import zipfile
from pathlib import Path

import pytest

from yonyou_doc2skill.cli.main import create_parser
from yonyou_doc2skill.cli.ikm_scraper import IKMToSkillConverter
from yonyou_doc2skill.cli.config_validator import ConfigValidator
from yonyou_doc2skill.cli.skill_converter import CONVERTER_REGISTRY
from yonyou_doc2skill.cli.unified_scraper import UnifiedScraper


class FakeResponse:
    def __init__(self, payload=None, content=b"", status_code=200):
        self._payload = payload
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        if self._payload is None:
            raise ValueError("No JSON payload")
        return self._payload


class FakeSession:
    def __init__(self):
        self.headers = {}
        self.post_calls = []
        self.get_calls = []

    def post(self, url, data=None, timeout=None):
        self.post_calls.append((url, data, timeout))
        if url.endswith("/knowledgemap/getKnowledgeMapByPK"):
            return FakeResponse(
                {
                    "code": "200",
                    "data": {
                        "pkMapview": "map-1",
                        "mapname": "数智焕新弹药库",
                        "mapdesc": "用于数智焕新战役的知识地图",
                        "operatororgname": "高端市场部",
                        "publishdate": "2025-04-30",
                    },
                }
            )
        if url.endswith("/knowledgemap/getMapData"):
            return FakeResponse(
                {
                    "code": "200",
                    "data": {
                        "numberOfElements": 1,
                        "totalPages": 1,
                        "mapCates": [{"catecode": "A", "catename": "战役一"}],
                        "pageList": [
                            {
                                "pkKnowledgeAsset": "asset-1",
                                "assetcode": "SC001",
                                "assetname": "财务数智化案例",
                                "knowledgeitemdes": "案例说明",
                                "detailnames": "案例PDF",
                                "filenum": 1,
                                "ownedrulename": "市场营销",
                                "ownedtypename": "营销工具",
                                "views": 12,
                                "downloads": 3,
                                "ownedername": "张三",
                            }
                        ],
                    },
                }
            )
        if url.endswith("/knowledge/portalAssets"):
            return FakeResponse(
                {
                    "code": "200",
                    "data": {
                        "pageList": [
                            {
                                "pkKnowledgeAsset": "portal-asset-1",
                                "assetname": "门户推荐案例",
                                "knowledgeitemdes": "门户栏目资产",
                                "filenum": 0,
                            }
                        ],
                    },
                }
            )
        if url.endswith("/knowledge/search"):
            return FakeResponse(
                {
                    "code": "200",
                    "data": {
                        "pageList": [
                            {
                                "pkKnowledgeAsset": "search-asset-1",
                                "assetname": "YonLinker 搜索结果",
                                "knowledgeitemdes": "搜索命中的资产",
                                "filenum": 0,
                            }
                        ],
                    },
                }
            )
        raise AssertionError(f"Unexpected POST {url}")

    def get(self, url, params=None, timeout=None):
        self.get_calls.append((url, params, timeout))
        if url.endswith("/file/getHlDetail"):
            return FakeResponse(
                {
                    "code": "200",
                    "data": [
                        {
                            "pkKnowledgeDetail": "detail-1",
                            "oridetailname": "案例说明.txt",
                            "detailtype": "txt",
                            "detailTypeCode": "TXT",
                            "applyState": 0,
                        }
                    ],
                }
            )
        if url.endswith("/file/downloadFileSingle"):
            return FakeResponse(content="附件正文：这里是交付案例的关键处理步骤。".encode())
        raise AssertionError(f"Unexpected GET {url}")


class FakeMixedAttachmentSession(FakeSession):
    def get(self, url, params=None, timeout=None):
        self.get_calls.append((url, params, timeout))
        if url.endswith("/file/getHlDetail"):
            return FakeResponse(
                {
                    "code": "200",
                    "data": [
                        {
                            "pkKnowledgeDetail": "detail-1",
                            "oridetailname": "案例说明.txt",
                            "detailtype": "txt",
                            "detailTypeCode": "TXT",
                            "applyState": 0,
                        },
                        {
                            "pkKnowledgeDetail": "video-1",
                            "oridetailname": "演示视频.mp4",
                            "detailtype": "mp4",
                            "detailTypeCode": "TE",
                            "applyState": 0,
                        },
                    ],
                }
            )
        if url.endswith("/file/downloadFileSingle"):
            return FakeResponse(content="附件正文：这里是交付案例的关键处理步骤。".encode())
        raise AssertionError(f"Unexpected GET {url}")


def test_ikm_parser_accepts_map_mode():
    parser = create_parser()

    args = parser.parse_args(
        [
            "ikm",
            "--base-url",
            "https://ikm.example.com",
            "--cookie",
            "u_token=abc",
            "--mode",
            "map",
            "--pk",
            "map-1",
            "--actionlocid",
            "portal-1",
            "--name",
            "ikm-map",
        ]
    )

    assert args.command == "ikm"
    assert args.mode == "map"
    assert args.pk == "map-1"


def test_ikm_parser_accepts_portal_and_search_modes():
    parser = create_parser()

    portal_args = parser.parse_args(
        [
            "ikm",
            "--cookie",
            "u_token=abc",
            "--mode",
            "portal",
            "--actionlocid",
            "portal-1",
            "--name",
            "ikm-portal",
        ]
    )
    search_args = parser.parse_args(
        [
            "ikm",
            "--cookie",
            "u_token=abc",
            "--mode",
            "search",
            "--keyword",
            "YonLinker",
            "--actionlocid",
            "portal-1",
            "--name",
            "ikm-search",
        ]
    )

    assert portal_args.mode == "portal"
    assert search_args.mode == "search"
    assert search_args.keyword == "YonLinker"


def test_ikm_parser_accepts_asset_url():
    parser = create_parser()

    args = parser.parse_args(
        [
            "ikm",
            "--cookie",
            "u_token=abc",
            "--mode",
            "asset",
            "--url",
            "https://ikm.example.com/forwardbase?actionloctype=portal&"
            "actionlocid=portal-1&path=eyJtb2R1bGUiOiJzY2VuZSJ9&"
            "pkasset=asset-1#/pages/km/usersystem/typicaldetail/typicaldetail",
            "--name",
            "ikm-asset",
        ]
    )

    assert args.mode == "asset"
    assert args.url.startswith("https://ikm.example.com/forwardbase")


def test_ikm_map_extraction_builds_skill(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    session = FakeSession()
    converter = IKMToSkillConverter(
        {
            "base_url": "https://ikm.example.com",
            "cookie": "u_token=abc",
            "mode": "map",
            "pk": "map-1",
            "actionlocid": "portal-1",
            "name": "ikm-map",
            "max_assets": 10,
            "download_attachments": True,
            "_session": session,
        }
    )

    assert converter.run() == 0

    skill_dir = Path("output/ikm-map")
    assert (skill_dir / "SKILL.md").exists()
    assert (skill_dir / "references/index.md").exists()
    assert (skill_dir / "references/assets.md").exists()
    assert (skill_dir / "references/attachments.md").exists()
    assert (skill_dir / "raw/map.json").exists()
    assert (skill_dir / "raw/assets.json").exists()
    assert (skill_dir / "downloads/detail-1.txt").exists()

    skill_md = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    assert "数智焕新弹药库" in skill_md
    assert "财务数智化案例" in (skill_dir / "references/assets.md").read_text(encoding="utf-8")
    assert "案例说明.txt" in (skill_dir / "references/attachments.md").read_text(
        encoding="utf-8"
    )

    extracted = json.loads(Path("output/ikm-map_extracted.json").read_text(encoding="utf-8"))
    assert extracted["map"]["mapname"] == "数智焕新弹药库"
    assert extracted["assets"][0]["attachments"][0]["pkKnowledgeDetail"] == "detail-1"
    download_calls = [
        call for call in session.get_calls if call[0].endswith("/file/downloadFileSingle")
    ]
    assert download_calls[0][1]["moduleobjname"] == "数智焕新弹药库"
    assert download_calls[0][1]["module"] == "mapview"


def test_ikm_parse_attachments_writes_reference_content(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    session = FakeSession()
    converter = IKMToSkillConverter(
        {
            "base_url": "https://ikm.example.com",
            "cookie": "u_token=abc",
            "mode": "map",
            "pk": "map-1",
            "actionlocid": "portal-1",
            "name": "ikm-map",
            "max_assets": 10,
            "parse_attachments": True,
            "_session": session,
        }
    )

    assert converter.run() == 0

    skill_dir = Path("output/ikm-map")
    assert (skill_dir / "references/content.md").exists()
    assert (skill_dir / "references/content/detail-1.md").exists()
    assert (skill_dir / "downloads/detail-1.txt").exists()

    content_index = (skill_dir / "references/content.md").read_text(encoding="utf-8")
    assert "附件正文：这里是交付案例的关键处理步骤。" in content_index

    skill_md = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    assert "references/content.md" in skill_md

    extracted = json.loads(Path("output/ikm-map_extracted.json").read_text(encoding="utf-8"))
    detail = extracted["assets"][0]["attachments"][0]
    assert detail["content_path"] == "references/content/detail-1.md"
    assert detail["content_chars"] > 0
    assert "parse_error" not in detail


def test_ikm_parse_attachments_skips_unparseable_downloads_by_default(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    session = FakeMixedAttachmentSession()
    converter = IKMToSkillConverter(
        {
            "base_url": "https://ikm.example.com",
            "cookie": "u_token=abc",
            "mode": "map",
            "pk": "map-1",
            "actionlocid": "portal-1",
            "name": "ikm-map",
            "max_assets": 10,
            "parse_attachments": True,
            "_session": session,
        }
    )

    assert converter.run() == 0

    extracted = json.loads(Path("output/ikm-map_extracted.json").read_text(encoding="utf-8"))
    attachments = extracted["assets"][0]["attachments"]
    assert attachments[0]["content_path"] == "references/content/detail-1.md"
    assert attachments[1]["download_skipped"] == "Skipped non-parseable attachment type: mp4"
    assert len([c for c in session.get_calls if c[0].endswith("/file/downloadFileSingle")]) == 1


def test_ikm_portal_extraction_builds_skill(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    converter = IKMToSkillConverter(
        {
            "base_url": "https://ikm.example.com",
            "cookie": "u_token=abc",
            "mode": "portal",
            "actionlocid": "portal-1",
            "name": "ikm-portal",
            "max_assets": 10,
            "portal_endpoint": "/knowledge/portalAssets",
            "_session": FakeSession(),
        }
    )

    assert converter.run() == 0

    extracted = json.loads(Path("output/ikm-portal_extracted.json").read_text(encoding="utf-8"))
    assert extracted["mode"] == "portal"
    assert extracted["assets"][0]["assetname"] == "门户推荐案例"
    assert "门户推荐案例" in Path("output/ikm-portal/references/assets.md").read_text(
        encoding="utf-8"
    )


def test_ikm_search_extraction_builds_skill(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    converter = IKMToSkillConverter(
        {
            "base_url": "https://ikm.example.com",
            "cookie": "u_token=abc",
            "mode": "search",
            "keyword": "YonLinker",
            "actionlocid": "portal-1",
            "name": "ikm-search",
            "max_assets": 10,
            "search_endpoint": "/knowledge/search",
            "_session": FakeSession(),
        }
    )

    assert converter.run() == 0

    extracted = json.loads(Path("output/ikm-search_extracted.json").read_text(encoding="utf-8"))
    assert extracted["mode"] == "search"
    assert extracted["keyword"] == "YonLinker"
    assert extracted["assets"][0]["assetname"] == "YonLinker 搜索结果"


def test_ikm_search_download_uses_search_module(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    session = FakeSession()
    converter = IKMToSkillConverter(
        {
            "base_url": "https://ikm.example.com",
            "cookie": "u_token=abc",
            "mode": "search",
            "keyword": "YonLinker",
            "actionlocid": "portal-1",
            "name": "ikm-search",
            "max_assets": 10,
            "search_endpoint": "/knowledge/search",
            "download_attachments": True,
            "_session": session,
        }
    )

    assert converter.run() == 0

    download_calls = [
        call for call in session.get_calls if call[0].endswith("/file/downloadFileSingle")
    ]
    assert download_calls[0][1]["module"] == "search"


def test_ikm_asset_url_extraction_builds_skill(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    session = FakeSession()
    converter = IKMToSkillConverter(
        {
            "base_url": "https://ikm.example.com",
            "cookie": "u_token=abc",
            "mode": "asset",
            "url": "https://ikm.example.com/forwardbase?actionloctype=portal&"
            "actionlocid=portal-1&path=eyJtb2R1bGUiOiJzY2VuZSJ9&"
            "pkasset=asset-1#/pages/km/usersystem/typicaldetail/typicaldetail",
            "name": "ikm-asset",
            "parse_attachments": True,
            "_session": session,
        }
    )

    assert converter.run() == 0

    extracted = json.loads(Path("output/ikm-asset_extracted.json").read_text(encoding="utf-8"))
    assert extracted["mode"] == "asset"
    assert extracted["asset"]["pkKnowledgeAsset"] == "asset-1"
    assert extracted["actionlocid"] == "portal-1"
    assert extracted["assets"][0]["attachments"][0]["content_path"] == (
        "references/content/detail-1.md"
    )

    download_calls = [
        call for call in session.get_calls if call[0].endswith("/file/downloadFileSingle")
    ]
    assert download_calls[0][1]["module"] == "scene"
    assert download_calls[0][1]["moduleobjid"] == ""


def test_ikm_docx_parser_uses_stdlib_fallback(tmp_path):
    docx_path = tmp_path / "sample.docx"
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>第一段交付知识</w:t></w:r></w:p>
    <w:p><w:r><w:t>第二段处理步骤</w:t></w:r></w:p>
  </w:body>
</w:document>
"""
    with zipfile.ZipFile(docx_path, "w") as docx_zip:
        docx_zip.writestr("word/document.xml", document_xml)

    converter = IKMToSkillConverter(
        {
            "base_url": "https://ikm.example.com",
            "cookie": "u_token=abc",
            "mode": "asset",
            "pk": "asset-1",
            "actionlocid": "portal-1",
            "name": "ikm-asset",
            "_session": FakeSession(),
        }
    )

    text = converter._extract_docx_text_stdlib(docx_path)
    assert "第一段交付知识" in text
    assert "第二段处理步骤" in text


def test_ikm_cookie_can_come_from_env(monkeypatch):
    monkeypatch.setenv("IKM_COOKIE", "u_token=env")

    converter = IKMToSkillConverter(
        {
            "base_url": "https://ikm.example.com",
            "mode": "map",
            "pk": "map-1",
            "actionlocid": "portal-1",
            "name": "ikm-map",
            "_session": FakeSession(),
        }
    )

    assert converter.cookie == "u_token=env"


def test_ikm_requires_cookie(monkeypatch):
    monkeypatch.delenv("IKM_COOKIE", raising=False)

    with pytest.raises(ValueError, match="cookie"):
        IKMToSkillConverter(
            {
                "base_url": "https://ikm.example.com",
                "mode": "map",
                "pk": "map-1",
                "actionlocid": "portal-1",
                "name": "ikm-map",
            }
        )


def test_ikm_from_json_does_not_require_cookie(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("IKM_COOKIE", raising=False)
    extracted = {
        "source_type": "ikm",
        "mode": "map",
        "base_url": "https://ikm.example.com",
        "actionloctype": "portal",
        "actionlocid": "portal-1",
        "map": {
            "pkMapview": "map-1",
            "mapname": "离线知识地图",
            "mapdesc": "从已抽取 JSON 构建",
        },
        "categories": [],
        "assets": [],
        "total_assets": 0,
    }
    source = Path("ikm.json")
    source.write_text(json.dumps(extracted, ensure_ascii=False), encoding="utf-8")

    converter = IKMToSkillConverter(
        {
            "base_url": "https://ikm.example.com",
            "mode": "map",
            "from_json": str(source),
            "name": "ikm-offline",
            "_session": FakeSession(),
        }
    )

    assert converter.run() == 0
    assert "离线知识地图" in Path("output/ikm-offline/SKILL.md").read_text(
        encoding="utf-8"
    )


def test_ikm_registered_as_converter_source():
    assert CONVERTER_REGISTRY["ikm"] == (
        "yonyou_doc2skill.cli.ikm_scraper",
        "IKMToSkillConverter",
    )


def test_ikm_config_validation_accepts_map_source():
    config = {
        "name": "ikm-project",
        "description": "IKM project",
        "sources": [
            {
                "type": "ikm",
                "base_url": "https://ikm.example.com",
                "mode": "map",
                "pk": "map-1",
                "actionlocid": "portal-1",
            }
        ],
    }

    assert ConfigValidator(config).validate() is True


def test_ikm_config_validation_accepts_portal_source():
    config = {
        "name": "ikm-project",
        "description": "IKM project",
        "sources": [
            {
                "type": "ikm",
                "base_url": "https://ikm.example.com",
                "mode": "portal",
                "actionlocid": "portal-1",
            }
        ],
    }

    assert ConfigValidator(config).validate() is True


def test_ikm_config_validation_accepts_search_source():
    config = {
        "name": "ikm-project",
        "description": "IKM project",
        "sources": [
            {
                "type": "ikm",
                "base_url": "https://ikm.example.com",
                "mode": "search",
                "keyword": "YonLinker",
                "actionlocid": "portal-1",
            }
        ],
    }

    assert ConfigValidator(config).validate() is True


def test_ikm_config_validation_requires_map_pk():
    config = {
        "name": "ikm-project",
        "description": "IKM project",
        "sources": [
            {
                "type": "ikm",
                "base_url": "https://ikm.example.com",
                "mode": "map",
                "actionlocid": "portal-1",
            }
        ],
    }

    with pytest.raises(ValueError, match="Missing required field 'pk'"):
        ConfigValidator(config).validate()


def test_ikm_config_validation_requires_search_keyword():
    config = {
        "name": "ikm-project",
        "description": "IKM project",
        "sources": [
            {
                "type": "ikm",
                "base_url": "https://ikm.example.com",
                "mode": "search",
                "actionlocid": "portal-1",
            }
        ],
    }

    with pytest.raises(ValueError, match="Missing required field 'keyword'"):
        ConfigValidator(config).validate()


def test_unified_scraper_dispatches_ikm_source(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("IKM_COOKIE", "u_token=env")
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "name": "mixed-ikm",
                "description": "Mixed IKM config",
                "sources": [
                    {
                        "type": "ikm",
                        "base_url": "https://ikm.example.com",
                        "mode": "map",
                        "pk": "map-1",
                        "actionlocid": "portal-1",
                        "max_assets": 5,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    scraper = UnifiedScraper(str(config_path))
    scraper._ikm_session_factory = FakeSession
    scraper.scrape_all_sources()

    assert scraper.scraped_data["ikm"][0]["source_id"] == "map-1"
    assert scraper.scraped_data["ikm"][0]["data"]["map"]["mapname"] == "数智焕新弹药库"
