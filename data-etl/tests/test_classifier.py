"""
Tests for technology classifier.
"""

import pytest
from unittest.mock import Mock, patch
from src.classifier import TechnologyClassifier


class TestTechnologyClassifier:
    """Test technology classification."""

    def setup_method(self):
        """Setup test fixtures."""
        self.config = {
            'openai': {
                'model': 'gpt-4o-mini',
                'max_tokens': 1000,
                'temperature': 0.3
            },
            'classification': {
                'thresholds': {
                    'adopt': 0.7,
                    'trial': 0.4,
                    'assess': 0.1
                },
                'min_repos': 2,
                'exclude_patterns': []
            }
        }
        self.classifier = TechnologyClassifier('fake-key', self.config)

    def test_determine_ring_adopt(self):
        """Test ring determination for high usage."""
        ring = self.classifier._determine_ring(75.0)
        assert ring == 0  # Adopt

    def test_determine_ring_trial(self):
        """Test ring determination for medium usage."""
        ring = self.classifier._determine_ring(50.0)
        assert ring == 1  # Trial

    def test_determine_ring_assess(self):
        """Test ring determination for low usage."""
        ring = self.classifier._determine_ring(20.0)
        assert ring == 2  # Assess

    def test_determine_ring_hold(self):
        """Test ring determination for very low usage."""
        ring = self.classifier._determine_ring(5.0)
        assert ring == 3  # Hold

    def test_infer_quadrant_language(self):
        """Test quadrant inference for languages."""
        quadrant = self.classifier._infer_quadrant('Python')
        assert quadrant == 3  # Languages & Frameworks

    def test_infer_quadrant_platform(self):
        """Test quadrant inference for platforms."""
        quadrant = self.classifier._infer_quadrant('Docker')
        assert quadrant == 2  # Platforms

    def test_infer_quadrant_tool(self):
        """Test quadrant inference for tools."""
        quadrant = self.classifier._infer_quadrant('Jest')
        assert quadrant == 1  # Tools

    def test_should_exclude(self):
        """Test exclusion patterns."""
        self.config['classification']['exclude_patterns'] = ['*-internal', 'custom-*']
        classifier = TechnologyClassifier('fake-key', self.config)

        assert classifier._should_exclude('tool-internal') is True
        assert classifier._should_exclude('custom-framework') is True
        assert classifier._should_exclude('React') is False

    def test_get_example_repos(self):
        """Test getting example repositories."""
        repo_details = [
            {'name': 'repo1', 'technologies': {'languages': {'Python'}}},
            {'name': 'repo2', 'technologies': {'languages': {'Python', 'JavaScript'}}},
            {'name': 'repo3', 'technologies': {'languages': {'JavaScript'}}},
        ]

        examples = self.classifier._get_example_repos('Python', repo_details, limit=5)

        assert 'repo1' in examples
        assert 'repo2' in examples
        assert len(examples) <= 2

    def test_fallback_classification(self):
        """Test fallback classification."""
        result = self.classifier._fallback_classification(
            'React',
            count=10,
            total_repos=20,
            usage_percentage=50.0,
            ring=1
        )

        assert result['name'] == 'React'
        assert result['ring'] == 1
        assert result['quadrant'] == 3  # Inferred as language/framework
        assert 'metadata' in result
        assert result['metadata']['repos_count'] == 10
        assert result['metadata']['usage_percentage'] == 50.0
