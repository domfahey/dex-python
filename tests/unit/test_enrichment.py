"""Tests for job title parsing and enrichment."""

from dex_python.enrichment import parse_job_title


class TestParseJobTitle:
    """Tests for parse_job_title function."""

    def test_simple_at_pattern(self) -> None:
        """Parse 'Role at Company' pattern."""
        result = parse_job_title("Software Engineer at Google")
        assert result["role"] == "Software Engineer"
        assert result["company"] == "Google"

    def test_at_symbol_pattern(self) -> None:
        """Parse 'Role @ Company' pattern."""
        result = parse_job_title("Developer @ Microsoft")
        assert result["role"] == "Developer"
        assert result["company"] == "Microsoft"

    def test_complex_role(self) -> None:
        """Parse complex role with multiple words."""
        title = "VP and NJ State Counsel at Fidelity National Title Group"
        result = parse_job_title(title)
        assert result["role"] == "VP and NJ State Counsel"
        assert result["company"] == "Fidelity National Title Group"

    def test_complex_company(self) -> None:
        """Parse company with punctuation."""
        title = "Legal Assistant/Paralegal at Davison Eastman Munoz Paone, P.A."
        result = parse_job_title(title)
        assert result["role"] == "Legal Assistant/Paralegal"
        assert result["company"] == "Davison Eastman Munoz Paone, P.A."

    def test_no_company_pattern(self) -> None:
        """Return full title as role when no company pattern."""
        result = parse_job_title("Senior Software Engineer")
        assert result["role"] == "Senior Software Engineer"
        assert result["company"] is None

    def test_empty_string(self) -> None:
        """Handle empty string."""
        result = parse_job_title("")
        assert result["role"] == ""
        assert result["company"] is None

    def test_none_input(self) -> None:
        """Handle None input."""
        result = parse_job_title(None)
        assert result["role"] is None
        assert result["company"] is None

    def test_case_insensitive(self) -> None:
        """Match 'AT' case-insensitively."""
        result = parse_job_title("Manager AT Acme Corp")
        assert result["role"] == "Manager"
        assert result["company"] == "Acme Corp"

    def test_multiple_at_uses_first(self) -> None:
        """When multiple 'at' present, split on first one."""
        result = parse_job_title("Director at Company at Location")
        assert result["role"] == "Director"
        assert result["company"] == "Company at Location"

    def test_strips_whitespace(self) -> None:
        """Strip extra whitespace from role and company."""
        result = parse_job_title("  Engineer   at   Startup  ")
        assert result["role"] == "Engineer"
        assert result["company"] == "Startup"

    def test_preserves_special_characters(self) -> None:
        """Preserve special characters in titles."""
        result = parse_job_title("VP, Sales & Marketing at Johnson & Johnson")
        assert result["role"] == "VP, Sales & Marketing"
        assert result["company"] == "Johnson & Johnson"
