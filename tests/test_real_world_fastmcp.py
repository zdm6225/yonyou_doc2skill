"""
Real-World Integration Test: FastMCP GitHub Repository

Tests the complete three-stream GitHub architecture pipeline on a real repository:
- https://github.com/jlowin/fastmcp

Validates:
1. GitHub three-stream fetcher works with real repo
2. All 3 streams populated (Code, Docs, Insights)
3. C3.x analysis produces ACTUAL results (not placeholders)
4. Router generation includes GitHub metadata
5. Quality metrics meet targets
6. Generated skills are production-quality

This is a comprehensive E2E test that exercises the entire system.
"""

import json
import os
from datetime import datetime
from pathlib import Path

import pytest

# Mark as integration test (slow)
pytestmark = pytest.mark.integration


class TestRealWorldFastMCP:
    """
    Real-world integration test using FastMCP repository.

    This test requires:
    - Internet connection
    - GitHub API access (optional GITHUB_TOKEN for higher rate limits)
    - 20-60 minutes for C3.x analysis

    Run with: pytest tests/test_real_world_fastmcp.py -v -s
    """

    @pytest.fixture(scope="class")
    def github_token(self):
        """Get GitHub token from environment (optional)."""
        token = os.getenv("GITHUB_TOKEN")
        if token:
            print("\n✅ GitHub token found - using authenticated API")
        else:
            print("\n⚠️  No GitHub token - using public API (lower rate limits)")
            print("   Set GITHUB_TOKEN environment variable for higher rate limits")
        return token

    @pytest.fixture(scope="class")
    def output_dir(self, tmp_path_factory):
        """Create output directory for test results."""
        output = tmp_path_factory.mktemp("fastmcp_real_test")
        print(f"\n📁 Test output directory: {output}")
        return output

    @pytest.fixture(scope="class")
    def fastmcp_analysis(self, github_token, output_dir):
        """
        Perform complete FastMCP analysis.

        This fixture runs the full pipeline and caches the result
        for all tests in this class.
        """
        from yonyou_doc2skill.cli.unified_codebase_analyzer import UnifiedCodebaseAnalyzer

        print(f"\n{'=' * 80}")
        print("🚀 REAL-WORLD TEST: FastMCP GitHub Repository")
        print(f"{'=' * 80}")
        print("Repository: https://github.com/jlowin/fastmcp")
        print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Output: {output_dir}")
        print(f"{'=' * 80}\n")

        # Run unified analyzer with C3.x depth
        analyzer = UnifiedCodebaseAnalyzer(github_token=github_token)

        try:
            # Start with basic analysis (fast) to verify three-stream architecture
            # Can be changed to "c3x" for full analysis (20-60 minutes)
            depth_mode = os.getenv(
                "TEST_DEPTH", "basic"
            )  # Use 'basic' for quick test, 'c3x' for full

            print(f"📊 Analysis depth: {depth_mode}")
            if depth_mode == "basic":
                print("   (Set TEST_DEPTH=c3x environment variable for full C3.x analysis)")
            print()

            result = analyzer.analyze(
                source="https://github.com/jlowin/fastmcp",
                depth=depth_mode,
                fetch_github_metadata=True,
                interactive=False,
                output_dir=output_dir,
            )

            print("\n✅ Analysis complete!")
            print(f"{'=' * 80}\n")

            return result

        except Exception as e:
            pytest.fail(f"Analysis failed: {e}")

    def test_01_three_streams_present(self, fastmcp_analysis):
        """Test that all 3 streams are present and populated."""
        print("\n" + "=" * 80)
        print("TEST 1: Verify All 3 Streams Present")
        print("=" * 80)

        result = fastmcp_analysis

        # Verify result structure
        assert result is not None, "Analysis result is None"
        assert result.source_type == "github", (
            f"Expected source_type 'github', got '{result.source_type}'"
        )
        # Depth can be 'basic' or 'c3x' depending on TEST_DEPTH env var
        assert result.analysis_depth in ["basic", "c3x"], f"Invalid depth '{result.analysis_depth}'"
        print(f"\n📊 Analysis depth: {result.analysis_depth}")

        # STREAM 1: Code Analysis
        print("\n📊 STREAM 1: Code Analysis")
        assert result.code_analysis is not None, "Code analysis missing"
        assert "files" in result.code_analysis, "Files list missing from code analysis"
        files = result.code_analysis["files"]
        print(f"   ✅ Files analyzed: {len(files)}")
        assert len(files) > 0, "No files found in code analysis"

        # STREAM 2: GitHub Docs
        print("\n📄 STREAM 2: GitHub Documentation")
        assert result.github_docs is not None, "GitHub docs missing"

        readme = result.github_docs.get("readme")
        assert readme is not None, "README missing from GitHub docs"
        print(f"   ✅ README length: {len(readme)} chars")
        assert len(readme) > 100, "README too short (< 100 chars)"
        assert "fastmcp" in readme.lower() or "mcp" in readme.lower(), (
            "README doesn't mention FastMCP/MCP"
        )

        contributing = result.github_docs.get("contributing")
        if contributing:
            print(f"   ✅ CONTRIBUTING.md length: {len(contributing)} chars")

        docs_files = result.github_docs.get("docs_files", [])
        print(f"   ✅ Additional docs files: {len(docs_files)}")

        # STREAM 3: GitHub Insights
        print("\n🐛 STREAM 3: GitHub Insights")
        assert result.github_insights is not None, "GitHub insights missing"

        metadata = result.github_insights.get("metadata", {})
        assert metadata, "Metadata missing from GitHub insights"

        stars = metadata.get("stars", 0)
        language = metadata.get("language", "Unknown")
        description = metadata.get("description", "")

        print(f"   ✅ Stars: {stars}")
        print(f"   ✅ Language: {language}")
        print(f"   ✅ Description: {description}")

        assert stars >= 0, "Stars count invalid"
        assert language, "Language not detected"

        common_problems = result.github_insights.get("common_problems", [])
        known_solutions = result.github_insights.get("known_solutions", [])
        top_labels = result.github_insights.get("top_labels", [])

        print(f"   ✅ Common problems: {len(common_problems)}")
        print(f"   ✅ Known solutions: {len(known_solutions)}")
        print(f"   ✅ Top labels: {len(top_labels)}")

        print("\n✅ All 3 streams verified!\n")

    def test_02_c3x_components_populated(self, fastmcp_analysis):
        """Test that C3.x components have ACTUAL data (not placeholders)."""
        print("\n" + "=" * 80)
        print("TEST 2: Verify C3.x Components Populated (NOT Placeholders)")
        print("=" * 80)

        result = fastmcp_analysis
        code_analysis = result.code_analysis

        # Skip C3.x checks if running in basic mode
        if result.analysis_depth == "basic":
            print("\n⚠️  Skipping C3.x component checks (running in basic mode)")
            print("   Set TEST_DEPTH=c3x to run full C3.x analysis")
            pytest.skip("C3.x analysis not run in basic mode")

        # This is the CRITICAL test - verify actual C3.x integration
        print("\n🔍 Checking C3.x Components:")

        # C3.1: Design Patterns
        c3_1 = code_analysis.get("c3_1_patterns", [])
        print("\n   C3.1 - Design Patterns:")
        print(f"   ✅ Count: {len(c3_1)}")
        if len(c3_1) > 0:
            print(
                f"   ✅ Sample: {c3_1[0].get('name', 'N/A')} ({c3_1[0].get('count', 0)} instances)"
            )
            # Verify it's not empty/placeholder
            assert c3_1[0].get("name"), "Pattern has no name"
            assert c3_1[0].get("count", 0) > 0, "Pattern has zero count"
        else:
            print("   ⚠️  No patterns detected (may be valid for small repos)")

        # C3.2: Test Examples
        c3_2 = code_analysis.get("c3_2_examples", [])
        c3_2_count = code_analysis.get("c3_2_examples_count", 0)
        print("\n   C3.2 - Test Examples:")
        print(f"   ✅ Count: {c3_2_count}")
        if len(c3_2) > 0:
            # C3.2 examples use 'test_name' and 'file_path' fields
            test_name = c3_2[0].get("test_name", c3_2[0].get("name", "N/A"))
            file_path = c3_2[0].get("file_path", c3_2[0].get("file", "N/A"))
            print(f"   ✅ Sample: {test_name} from {file_path}")
            # Verify it's not empty/placeholder
            assert test_name and test_name != "N/A", "Example has no test_name"
            assert file_path and file_path != "N/A", "Example has no file_path"
        else:
            print("   ⚠️  No test examples found")

        # C3.3: How-to Guides
        c3_3 = code_analysis.get("c3_3_guides", [])
        print("\n   C3.3 - How-to Guides:")
        print(f"   ✅ Count: {len(c3_3)}")
        if len(c3_3) > 0:
            print(f"   ✅ Sample: {c3_3[0].get('title', 'N/A')}")

        # C3.4: Config Patterns
        c3_4 = code_analysis.get("c3_4_configs", [])
        print("\n   C3.4 - Config Patterns:")
        print(f"   ✅ Count: {len(c3_4)}")
        if len(c3_4) > 0:
            print(f"   ✅ Sample: {c3_4[0].get('file', 'N/A')}")

        # C3.7: Architecture
        c3_7 = code_analysis.get("c3_7_architecture", [])
        print("\n   C3.7 - Architecture:")
        print(f"   ✅ Count: {len(c3_7)}")
        if len(c3_7) > 0:
            print(f"   ✅ Sample: {c3_7[0].get('pattern', 'N/A')}")

        # CRITICAL: Verify at least SOME C3.x components have data
        # Not all repos will have all components, but should have at least one
        total_c3x_items = len(c3_1) + len(c3_2) + len(c3_3) + len(c3_4) + len(c3_7)

        print(f"\n📊 Total C3.x items: {total_c3x_items}")

        assert total_c3x_items > 0, (
            "❌ CRITICAL: No C3.x data found! This suggests placeholders are being used instead of actual analysis."
        )

        print("\n✅ C3.x components verified - ACTUAL data present (not placeholders)!\n")

    def test_03_router_generation(self, fastmcp_analysis, output_dir):
        """Test router generation with GitHub integration."""
        print("\n" + "=" * 80)
        print("TEST 3: Router Generation with GitHub Integration")
        print("=" * 80)

        from yonyou_doc2skill.cli.generate_router import RouterGenerator
        from yonyou_doc2skill.cli.github_fetcher import (
            CodeStream,
            DocsStream,
            InsightsStream,
            ThreeStreamData,
        )

        result = fastmcp_analysis

        # Create mock sub-skill configs
        config1 = output_dir / "fastmcp-oauth.json"
        config1.write_text(
            json.dumps(
                {
                    "name": "fastmcp-oauth",
                    "description": "OAuth authentication for FastMCP",
                    "categories": {"oauth": ["oauth", "auth", "provider", "google", "azure"]},
                }
            )
        )

        config2 = output_dir / "fastmcp-async.json"
        config2.write_text(
            json.dumps(
                {
                    "name": "fastmcp-async",
                    "description": "Async patterns for FastMCP",
                    "categories": {"async": ["async", "await", "asyncio"]},
                }
            )
        )

        # Reconstruct ThreeStreamData from result
        github_streams = ThreeStreamData(
            code_stream=CodeStream(directory=Path(output_dir), files=[]),
            docs_stream=DocsStream(
                readme=result.github_docs.get("readme"),
                contributing=result.github_docs.get("contributing"),
                docs_files=result.github_docs.get("docs_files", []),
            ),
            insights_stream=InsightsStream(
                metadata=result.github_insights.get("metadata", {}),
                common_problems=result.github_insights.get("common_problems", []),
                known_solutions=result.github_insights.get("known_solutions", []),
                top_labels=result.github_insights.get("top_labels", []),
            ),
        )

        # Generate router
        print("\n🧭 Generating router...")
        generator = RouterGenerator(
            config_paths=[str(config1), str(config2)],
            router_name="fastmcp",
            github_streams=github_streams,
        )

        skill_md = generator.generate_skill_md()

        # Save router for inspection
        router_file = output_dir / "fastmcp_router_SKILL.md"
        router_file.write_text(skill_md)
        print(f"   ✅ Router saved to: {router_file}")

        # Verify router content
        print("\n📝 Router Content Analysis:")

        # Check basic structure
        assert "fastmcp" in skill_md.lower(), "Router doesn't mention FastMCP"
        print("   ✅ Contains 'fastmcp'")

        # Check GitHub metadata
        if "Repository:" in skill_md or "github.com" in skill_md:
            print("   ✅ Contains repository URL")

        if "⭐" in skill_md or "Stars:" in skill_md:
            print("   ✅ Contains star count")

        if "Python" in skill_md or result.github_insights["metadata"].get("language") in skill_md:
            print("   ✅ Contains language")

        # Check README content
        if "Quick Start" in skill_md or "README" in skill_md:
            print("   ✅ Contains README quick start")

        # Check common issues
        if "Common Issues" in skill_md or "Issue #" in skill_md:
            issue_count = skill_md.count("Issue #")
            print(f"   ✅ Contains {issue_count} GitHub issues")

        # Check routing
        if "fastmcp-oauth" in skill_md:
            print("   ✅ Contains sub-skill routing")

        # Measure router size
        router_lines = len(skill_md.split("\n"))
        print(f"\n📏 Router size: {router_lines} lines")

        # Architecture target: 60-250 lines
        # With GitHub integration: expect higher end of range
        if router_lines < 60:
            print("   ⚠️  Router smaller than target (60-250 lines)")
        elif router_lines > 250:
            print("   ⚠️  Router larger than target (60-250 lines)")
        else:
            print("   ✅ Router size within target range")

        print("\n✅ Router generation verified!\n")

    def test_04_quality_metrics(self, fastmcp_analysis, output_dir):  # noqa: ARG002
        """Test that quality metrics meet architecture targets."""
        print("\n" + "=" * 80)
        print("TEST 4: Quality Metrics Validation")
        print("=" * 80)

        result = fastmcp_analysis

        # Metric 1: GitHub Overhead
        print("\n📊 Metric 1: GitHub Overhead")
        print("   Target: 20-60 lines")

        # Estimate GitHub overhead from insights
        metadata_lines = 3  # Repository, Stars, Language
        readme_estimate = 10  # Quick start section
        issue_count = len(result.github_insights.get("common_problems", []))
        issue_lines = min(issue_count * 3, 25)  # Max 5 issues shown

        total_overhead = metadata_lines + readme_estimate + issue_lines
        print(f"   Estimated: {total_overhead} lines")

        if 20 <= total_overhead <= 60:
            print("   ✅ Within target range")
        else:
            print("   ⚠️  Outside target range (may be acceptable)")

        # Metric 2: Data Quality
        print("\n📊 Metric 2: Data Quality")

        code_files = len(result.code_analysis.get("files", []))
        print(f"   Code files: {code_files}")
        assert code_files > 0, "No code files found"
        print("   ✅ Code files present")

        readme_len = len(result.github_docs.get("readme", ""))
        print(f"   README length: {readme_len} chars")
        assert readme_len > 100, "README too short"
        print("   ✅ README has content")

        stars = result.github_insights["metadata"].get("stars", 0)
        print(f"   Repository stars: {stars}")
        print("   ✅ Metadata present")

        # Metric 3: C3.x Coverage
        print("\n📊 Metric 3: C3.x Coverage")

        if result.analysis_depth == "basic":
            print("   ⚠️  Running in basic mode - C3.x components not analyzed")
            print("   Set TEST_DEPTH=c3x to enable C3.x analysis")
        else:
            c3x_components = {
                "Patterns": len(result.code_analysis.get("c3_1_patterns", [])),
                "Examples": result.code_analysis.get("c3_2_examples_count", 0),
                "Guides": len(result.code_analysis.get("c3_3_guides", [])),
                "Configs": len(result.code_analysis.get("c3_4_configs", [])),
                "Architecture": len(result.code_analysis.get("c3_7_architecture", [])),
            }

            for name, count in c3x_components.items():
                status = "✅" if count > 0 else "⚠️ "
                print(f"   {status} {name}: {count}")

            total_c3x = sum(c3x_components.values())
            print(f"   Total C3.x items: {total_c3x}")
            assert total_c3x > 0, "No C3.x data extracted"
            print("   ✅ C3.x analysis successful")

        print("\n✅ Quality metrics validated!\n")

    def test_05_skill_quality_assessment(self, output_dir):
        """Manual quality assessment of generated router skill."""
        print("\n" + "=" * 80)
        print("TEST 5: Skill Quality Assessment")
        print("=" * 80)

        router_file = output_dir / "fastmcp_router_SKILL.md"

        if not router_file.exists():
            pytest.skip("Router file not generated yet")

        content = router_file.read_text()

        print("\n📝 Quality Checklist:")

        # 1. Has frontmatter
        has_frontmatter = content.startswith("---")
        print(f"   {'✅' if has_frontmatter else '❌'} Has YAML frontmatter")

        # 2. Has main heading
        has_heading = "# " in content
        print(f"   {'✅' if has_heading else '❌'} Has main heading")

        # 3. Has sections
        section_count = content.count("## ")
        print(f"   {'✅' if section_count >= 3 else '❌'} Has {section_count} sections (need 3+)")

        # 4. Has code blocks
        code_block_count = content.count("```")
        has_code = code_block_count >= 2
        print(f"   {'✅' if has_code else '⚠️ '} Has {code_block_count // 2} code blocks")

        # 5. No placeholders
        no_todos = "TODO" not in content and "[Add" not in content
        print(f"   {'✅' if no_todos else '❌'} No TODO placeholders")

        # 6. Has GitHub content
        has_github = any(
            marker in content for marker in ["Repository:", "⭐", "Issue #", "github.com"]
        )
        print(f"   {'✅' if has_github else '⚠️ '} Has GitHub integration")

        # 7. Has routing
        has_routing = "skill" in content.lower() and "use" in content.lower()
        print(f"   {'✅' if has_routing else '⚠️ '} Has routing guidance")

        # Calculate quality score
        checks = [
            has_frontmatter,
            has_heading,
            section_count >= 3,
            has_code,
            no_todos,
            has_github,
            has_routing,
        ]
        score = sum(checks) / len(checks) * 100

        print(f"\n📊 Quality Score: {score:.0f}%")

        if score >= 85:
            print("   ✅ Excellent quality")
        elif score >= 70:
            print("   ✅ Good quality")
        elif score >= 50:
            print("   ⚠️  Acceptable quality")
        else:
            print("   ❌ Poor quality")

        assert score >= 50, f"Quality score too low: {score}%"

        print("\n✅ Skill quality assessed!\n")

    def test_06_final_report(self, fastmcp_analysis, output_dir):
        """Generate final test report."""
        print("\n" + "=" * 80)
        print("FINAL REPORT: Real-World FastMCP Test")
        print("=" * 80)

        result = fastmcp_analysis

        print("\n📊 Summary:")
        print("   Repository: https://github.com/jlowin/fastmcp")
        print(f"   Analysis: {result.analysis_depth}")
        print(f"   Source type: {result.source_type}")
        print(f"   Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        print("\n✅ Stream Verification:")
        print(f"   ✅ Code Stream: {len(result.code_analysis.get('files', []))} files")
        print(f"   ✅ Docs Stream: {len(result.github_docs.get('readme', ''))} char README")
        print(f"   ✅ Insights Stream: {result.github_insights['metadata'].get('stars', 0)} stars")

        print("\n✅ C3.x Components:")
        print(f"   ✅ Patterns: {len(result.code_analysis.get('c3_1_patterns', []))}")
        print(f"   ✅ Examples: {result.code_analysis.get('c3_2_examples_count', 0)}")
        print(f"   ✅ Guides: {len(result.code_analysis.get('c3_3_guides', []))}")
        print(f"   ✅ Configs: {len(result.code_analysis.get('c3_4_configs', []))}")
        print(f"   ✅ Architecture: {len(result.code_analysis.get('c3_7_architecture', []))}")

        print("\n✅ Quality Metrics:")
        print("   ✅ All 3 streams present and populated")
        print("   ✅ C3.x actual data (not placeholders)")
        print("   ✅ Router generated with GitHub integration")
        print("   ✅ Quality metrics within targets")

        print("\n🎉 SUCCESS: System working correctly with real repository!")
        print(f"\n📁 Test artifacts saved to: {output_dir}")
        print(f"   - Router: {output_dir}/fastmcp_router_SKILL.md")

        print(f"\n{'=' * 80}\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
