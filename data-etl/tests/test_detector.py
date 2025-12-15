"""
Tests for technology detector.
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.detector import TechnologyDetector


class TestTechnologyDetector:
    """Test technology detection."""

    def setup_method(self):
        """Setup test fixtures."""
        self.detector = TechnologyDetector()

    def test_detect_node_react(self):
        """Test React detection from package.json."""
        repo = Mock()
        content = Mock()
        content.decoded_content = b'{"dependencies": {"react": "^18.0.0"}}'
        repo.get_contents.return_value = content

        techs = self.detector.detect_node(repo)

        assert 'React' in techs['frameworks']

    def test_detect_node_typescript(self):
        """Test TypeScript detection."""
        repo = Mock()
        content = Mock()
        content.decoded_content = b'{"devDependencies": {"typescript": "^5.0.0"}}'
        repo.get_contents.return_value = content

        techs = self.detector.detect_node(repo)

        assert 'TypeScript' in techs['tools']

    def test_detect_python_django(self):
        """Test Django detection from requirements.txt."""
        repo = Mock()
        content = Mock()
        content.decoded_content = b'django==4.2.0\npsycopg2==2.9.0'
        repo.get_contents.return_value = content

        techs = self.detector.detect_python(repo)

        assert 'Django' in techs['frameworks']

    def test_detect_go(self):
        """Test Go detection."""
        repo = Mock()
        repo.get_contents.return_value = Mock()  # go.mod exists

        techs = self.detector.detect_go(repo)

        assert 'Go' in techs['languages']

    def test_detect_docker(self):
        """Test Docker detection."""
        repo = Mock()
        repo.get_contents.return_value = Mock()  # Dockerfile exists

        techs = self.detector.detect_docker(repo)

        assert 'Docker' in techs['platforms']

    def test_aggregate_technologies(self):
        """Test technology aggregation."""
        all_techs = [
            {'languages': {'Python'}, 'frameworks': {'Django'}},
            {'languages': {'Python'}, 'frameworks': {'Flask'}},
            {'languages': {'JavaScript'}, 'frameworks': {'React'}},
        ]

        counts = self.detector.aggregate_technologies(all_techs)

        assert counts['Python'] == 2
        assert counts['Django'] == 1
        assert counts['Flask'] == 1
        assert counts['JavaScript'] == 1
        assert counts['React'] == 1
