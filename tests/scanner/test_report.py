"""reportモジュールのユニットテスト。"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.scanner.report import (
    convert_zap_to_report_data,
    generate_security_report,
    load_zap_json,
    render_html_report,
)


class TestLoadZapJson:
    """load_zap_json関数のテストクラス。"""

    def test_load_valid_json(self, tmp_path):
        """有効なJSONファイルを読み込むことをテスト。"""
        # テスト用のJSONデータを作成
        test_data = {
            "site": [{"@name": "http://example.com", "alerts": []}],
            "created": "2025-11-23T01:41:56Z",
        }

        json_file = tmp_path / "test.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        # 関数を実行
        result = load_zap_json.fn(json_file)

        assert result == test_data
        assert "site" in result
        assert "created" in result

    def test_load_json_with_utf8_encoding(self, tmp_path):
        """UTF-8エンコーディングで日本語を含むJSONを読み込むことをテスト。"""
        test_data = {
            "site": [{"@name": "テストサイト", "alerts": []}],
            "created": "2025-11-23T01:41:56Z",
        }

        json_file = tmp_path / "test_jp.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False)

        result = load_zap_json.fn(json_file)

        assert result["site"][0]["@name"] == "テストサイト"


class TestConvertZapToReportData:
    """convert_zap_to_report_data関数のテストクラス。"""

    def test_basic_conversion(self):
        """基本的なデータ変換をテスト。"""
        zap_data = {
            "site": [
                {
                    "@name": "http://example.com",
                    "alerts": [
                        {
                            "alert": "Test Alert",
                            "riskdesc": "High",
                            "count": "1",
                            "instances": [{"uri": "http://example.com/test"}],
                            "desc": "<p>Test description</p>",
                            "solution": "<p>Test solution</p>",
                            "reference": "",
                        }
                    ],
                }
            ],
            "created": "2025-11-23T01:41:56Z",
        }

        result = convert_zap_to_report_data.fn(zap_data)

        assert result["site"] == "http://example.com"
        assert result["date"] == "2025/11/23 10:41:56"  # UTC+9
        assert len(result["summary"]) == 1
        assert len(result["alerts"]) == 1
        assert result["summary"][0]["name"] == "Test Alert"
        assert result["summary"][0]["risk"] == "High"

    def test_risk_level_conversion_japanese(self):
        """日本語のrisk levelを英語に変換することをテスト。"""
        zap_data = {
            "site": [
                {
                    "@name": "http://example.com",
                    "alerts": [
                        {"alert": "高リスク", "riskdesc": "高 (High)", "instances": []},
                        {"alert": "中リスク", "riskdesc": "中 (Medium)", "instances": []},
                        {"alert": "低リスク", "riskdesc": "低 (Low)", "instances": []},
                        {
                            "alert": "情報",
                            "riskdesc": "情報 (Informational)",
                            "instances": [],
                        },
                    ],
                }
            ],
            "created": "",
        }

        result = convert_zap_to_report_data.fn(zap_data)

        assert result["alerts"][0]["risk"] == "High"
        assert result["alerts"][1]["risk"] == "Medium"
        assert result["alerts"][2]["risk"] == "Low"
        assert result["alerts"][3]["risk"] == "Informational"

    def test_unique_url_counting(self):
        """重複するURLを正しくカウントすることをテスト。"""
        zap_data = {
            "site": [
                {
                    "@name": "http://example.com",
                    "alerts": [
                        {
                            "alert": "Test Alert",
                            "riskdesc": "High",
                            "instances": [
                                {"uri": "http://example.com/page1"},
                                {"uri": "http://example.com/page1"},  # 重複
                                {"uri": "http://example.com/page2"},
                            ],
                        }
                    ],
                }
            ],
            "created": "",
        }

        result = convert_zap_to_report_data.fn(zap_data)

        # 重複を除いた2つのユニークURLをカウント
        assert result["summary"][0]["urls"] == 2

    def test_severity_sorting(self):
        """アラートが重要度順にソートされることをテスト。"""
        zap_data = {
            "site": [
                {
                    "@name": "http://example.com",
                    "alerts": [
                        {"alert": "Low Alert", "riskdesc": "Low", "instances": []},
                        {"alert": "High Alert", "riskdesc": "High", "instances": []},
                        {"alert": "Medium Alert", "riskdesc": "Medium", "instances": []},
                        {
                            "alert": "Info Alert",
                            "riskdesc": "Informational",
                            "instances": [],
                        },
                    ],
                }
            ],
            "created": "",
        }

        result = convert_zap_to_report_data.fn(zap_data)

        # High -> Medium -> Low -> Informational の順にソート
        assert result["alerts"][0]["name"] == "High Alert"
        assert result["alerts"][1]["name"] == "Medium Alert"
        assert result["alerts"][2]["name"] == "Low Alert"
        assert result["alerts"][3]["name"] == "Info Alert"

    def test_html_tag_removal(self):
        """HTMLタグが正しく除去されることをテスト。"""
        zap_data = {
            "site": [
                {
                    "@name": "http://example.com",
                    "alerts": [
                        {
                            "alert": "Test",
                            "riskdesc": "High",
                            "instances": [],
                            "desc": "<p>Test <b>description</b></p>",
                            "solution": "<p>Test <i>solution</i></p>",
                            "reference": "<p>http://example.com</p>",
                        }
                    ],
                }
            ],
            "created": "",
        }

        result = convert_zap_to_report_data.fn(zap_data)

        # <p>タグのみ除去（他のタグは残る）
        assert result["alerts"][0]["description"] == "Test <b>description</b>"
        assert result["alerts"][0]["solution"] == "Test <i>solution</i>"

    def test_reference_url_extraction(self):
        """参照URLが正しく抽出されることをテスト。"""
        zap_data = {
            "site": [
                {
                    "@name": "http://example.com",
                    "alerts": [
                        {
                            "alert": "Test",
                            "riskdesc": "High",
                            "instances": [],
                            "reference": "<p>https://example.com/ref1 https://example.com/ref2</p>",
                        }
                    ],
                }
            ],
            "created": "",
        }

        result = convert_zap_to_report_data.fn(zap_data)

        assert len(result["alerts"][0]["reference_urls"]) == 2
        assert "https://example.com/ref1" in result["alerts"][0]["reference_urls"]
        assert "https://example.com/ref2" in result["alerts"][0]["reference_urls"]

    def test_optional_instance_fields(self):
        """オプショナルなインスタンスフィールドが正しく処理されることをテスト。"""
        zap_data = {
            "site": [
                {
                    "@name": "http://example.com",
                    "alerts": [
                        {
                            "alert": "Test",
                            "riskdesc": "High",
                            "instances": [
                                {
                                    "uri": "http://example.com",
                                    "method": "GET",
                                    "param": "id",
                                    "attack": "' OR '1'='1",
                                    "evidence": "error",
                                    "otherinfo": "extra info",
                                },
                                {
                                    "uri": "http://example.com/minimal",
                                    "method": "POST",
                                    # param, attack, evidence, otherinfo なし
                                },
                            ],
                        }
                    ],
                }
            ],
            "created": "",
        }

        result = convert_zap_to_report_data.fn(zap_data)

        # 最初のインスタンスは全フィールドを持つ
        first_instance = result["alerts"][0]["instances"][0]
        assert "param" in first_instance
        assert "attack" in first_instance
        assert "evidence" in first_instance
        assert "otherinfo" in first_instance

        # 2番目のインスタンスは必須フィールドのみ
        second_instance = result["alerts"][0]["instances"][1]
        assert "param" not in second_instance
        assert "attack" not in second_instance
        assert "evidence" not in second_instance
        assert "otherinfo" not in second_instance

    def test_score_calculation_perfect(self):
        """アラートがない場合の完璧なスコア(100点)をテスト。"""
        zap_data = {
            "site": [{"@name": "http://example.com", "alerts": []}],
            "created": "",
        }

        result = convert_zap_to_report_data.fn(zap_data)

        assert result["score"] == 100
        assert result["grade"] == "A"
        assert result["grade_color"] == "green"

    def test_score_calculation_grade_a(self):
        """グレードA (80点以上) の計算をテスト。"""
        # 80点: High×1 = -20点
        zap_data = {
            "site": [
                {
                    "@name": "http://example.com",
                    "alerts": [
                        {"alert": "High1", "riskdesc": "High", "instances": []},
                    ],
                }
            ],
            "created": "",
        }

        result = convert_zap_to_report_data.fn(zap_data)

        assert result["score"] == 80
        assert result["grade"] == "A"
        assert result["grade_color"] == "green"

    def test_score_calculation_grade_b(self):
        """グレードB (60-79点) の計算をテスト。"""
        # 60点: High×2 = -40点
        zap_data = {
            "site": [
                {
                    "@name": "http://example.com",
                    "alerts": [
                        {"alert": "High1", "riskdesc": "High", "instances": []},
                        {"alert": "High2", "riskdesc": "High", "instances": []},
                    ],
                }
            ],
            "created": "",
        }

        result = convert_zap_to_report_data.fn(zap_data)

        assert result["score"] == 60
        assert result["grade"] == "B"
        assert result["grade_color"] == "blue"

    def test_score_calculation_grade_c(self):
        """グレードC (40-59点) の計算をテスト。"""
        # 40点: High×3 = -60点
        zap_data = {
            "site": [
                {
                    "@name": "http://example.com",
                    "alerts": [
                        {"alert": "High1", "riskdesc": "High", "instances": []},
                        {"alert": "High2", "riskdesc": "High", "instances": []},
                        {"alert": "High3", "riskdesc": "High", "instances": []},
                    ],
                }
            ],
            "created": "",
        }

        result = convert_zap_to_report_data.fn(zap_data)

        assert result["score"] == 40
        assert result["grade"] == "C"
        assert result["grade_color"] == "yellow"

    def test_score_calculation_grade_d(self):
        """グレードD (20-39点) の計算をテスト。"""
        # 20点: High×4 = -80点
        zap_data = {
            "site": [
                {
                    "@name": "http://example.com",
                    "alerts": [
                        {"alert": "High1", "riskdesc": "High", "instances": []},
                        {"alert": "High2", "riskdesc": "High", "instances": []},
                        {"alert": "High3", "riskdesc": "High", "instances": []},
                        {"alert": "High4", "riskdesc": "High", "instances": []},
                    ],
                }
            ],
            "created": "",
        }

        result = convert_zap_to_report_data.fn(zap_data)

        assert result["score"] == 20
        assert result["grade"] == "D"
        assert result["grade_color"] == "orange"

    def test_score_calculation_grade_e(self):
        """グレードE (1-19点) の計算をテスト。"""
        # 14点: High×4 + Medium×2 = -80-6 = -86点 → 100-86 = 14点
        zap_data = {
            "site": [
                {
                    "@name": "http://example.com",
                    "alerts": [
                        {"alert": "High1", "riskdesc": "High", "instances": []},
                        {"alert": "High2", "riskdesc": "High", "instances": []},
                        {"alert": "High3", "riskdesc": "High", "instances": []},
                        {"alert": "High4", "riskdesc": "High", "instances": []},
                        {"alert": "Medium1", "riskdesc": "Medium", "instances": []},
                        {"alert": "Medium2", "riskdesc": "Medium", "instances": []},
                    ],
                }
            ],
            "created": "",
        }

        result = convert_zap_to_report_data.fn(zap_data)

        assert result["score"] == 14
        assert result["grade"] == "E"
        assert result["grade_color"] == "red"

    def test_score_calculation_grade_f(self):
        """グレードF (0点) の計算をテスト。"""
        # 0点: High×5 = -100点
        zap_data = {
            "site": [
                {
                    "@name": "http://example.com",
                    "alerts": [
                        {"alert": f"High{i}", "riskdesc": "High", "instances": []}
                        for i in range(5)
                    ],
                }
            ],
            "created": "",
        }

        result = convert_zap_to_report_data.fn(zap_data)

        assert result["score"] == 0
        assert result["grade"] == "F"
        assert result["grade_color"] == "red"

    def test_score_calculation_mixed_severity(self):
        """複数の重要度が混在する場合の計算をテスト。"""
        # 100 - (High×1×20 + Medium×2×3 + Low×4×1) = 100 - 30 = 70点
        zap_data = {
            "site": [
                {
                    "@name": "http://example.com",
                    "alerts": [
                        {"alert": "High1", "riskdesc": "High", "instances": []},
                        {"alert": "Medium1", "riskdesc": "Medium", "instances": []},
                        {"alert": "Medium2", "riskdesc": "Medium", "instances": []},
                        {"alert": "Low1", "riskdesc": "Low", "instances": []},
                        {"alert": "Low2", "riskdesc": "Low", "instances": []},
                        {"alert": "Low3", "riskdesc": "Low", "instances": []},
                        {"alert": "Low4", "riskdesc": "Low", "instances": []},
                    ],
                }
            ],
            "created": "",
        }

        result = convert_zap_to_report_data.fn(zap_data)

        assert result["score"] == 70
        assert result["grade"] == "B"

    def test_score_calculation_clamped_to_zero(self):
        """スコアが負になる場合、0にクランプされることをテスト。"""
        # 100 - (High×10×20) = -100 → 0にクランプ
        zap_data = {
            "site": [
                {
                    "@name": "http://example.com",
                    "alerts": [
                        {"alert": f"High{i}", "riskdesc": "High", "instances": []}
                        for i in range(10)
                    ],
                }
            ],
            "created": "",
        }

        result = convert_zap_to_report_data.fn(zap_data)

        assert result["score"] == 0
        assert result["grade"] == "F"


class TestRenderHtmlReport:
    """render_html_report関数のテストクラス。"""

    def test_render_basic_html(self, tmp_path):
        """基本的なHTMLレンダリングをテスト。"""
        # テンプレートディレクトリとファイルを作成
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        template_file = template_dir / "report.html.j2"
        template_content = """
        <html>
        <body>
            <h1>{{ site }}</h1>
            <p>Date: {{ date }}</p>
            <p>Alerts: {{ alerts|length }}</p>
        </body>
        </html>
        """
        template_file.write_text(template_content)

        # レポートデータ
        report_data = {
            "site": "http://example.com",
            "date": "2025/11/23 10:41:56",
            "summary": [],
            "alerts": [{"name": "Test Alert"}],
        }

        # 出力パス
        output_path = tmp_path / "output.html"

        # 関数を実行
        result_path = render_html_report.fn(report_data, template_dir, output_path)

        # 検証
        assert result_path == output_path
        assert output_path.exists()

        html_content = output_path.read_text()
        assert "http://example.com" in html_content
        assert "2025/11/23 10:41:56" in html_content
        assert "Alerts: 1" in html_content


class TestGenerateSecurityReport:
    """generate_security_report関数のテストクラス。"""

    def test_generate_report_with_default_output_path(self, tmp_path):
        """デフォルトの出力パスでレポート生成をテスト。"""
        # ZAP JSONファイルを作成
        json_file = tmp_path / "scan-report.json"
        zap_data = {
            "site": [{"@name": "http://example.com", "alerts": []}],
            "created": "2025-11-23T01:41:56Z",
        }
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(zap_data, f)

        # テンプレートディレクトリを作成
        # プロジェクトルートからの相対パスでテンプレートを配置
        project_root = Path(__file__).parent.parent.parent
        template_dir = project_root / "resources" / "templates"

        # テンプレートが存在しない場合はスキップ
        if not (template_dir / "report.html.j2").exists():
            pytest.skip("Template file not found")

        # 関数を実行（Prefectのflowをバイパスしてテスト）
        with patch("src.scanner.report.load_zap_json") as mock_load, patch(
            "src.scanner.report.convert_zap_to_report_data"
        ) as mock_convert, patch("src.scanner.report.render_html_report") as mock_render:
            mock_load.return_value = zap_data
            mock_convert.return_value = {
                "site": "http://example.com",
                "date": "2025/11/23 10:41:56",
                "summary": [],
                "alerts": [],
            }
            mock_render.return_value = tmp_path / "security-report.html"

            generate_security_report(json_file)

            # デフォルトのoutput_pathが使用されたことを確認
            expected_output = json_file.parent / "security-report.html"
            mock_render.assert_called_once()
            assert mock_render.call_args[0][2] == expected_output

    def test_generate_report_with_custom_output_path(self, tmp_path):
        """カスタム出力パスでレポート生成をテスト。"""
        # ZAP JSONファイルを作成
        json_file = tmp_path / "scan-report.json"
        zap_data = {
            "site": [{"@name": "http://example.com", "alerts": []}],
            "created": "2025-11-23T01:41:56Z",
        }
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(zap_data, f)

        custom_output = tmp_path / "custom-report.html"

        with patch("src.scanner.report.load_zap_json") as mock_load, patch(
            "src.scanner.report.convert_zap_to_report_data"
        ) as mock_convert, patch("src.scanner.report.render_html_report") as mock_render:
            mock_load.return_value = zap_data
            mock_convert.return_value = {
                "site": "http://example.com",
                "date": "2025/11/23 10:41:56",
                "summary": [],
                "alerts": [],
            }
            mock_render.return_value = custom_output

            generate_security_report(json_file, custom_output)

            # カスタムoutput_pathが使用されたことを確認
            mock_render.assert_called_once()
            assert mock_render.call_args[0][2] == custom_output
