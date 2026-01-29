"""Tests for TemplateAnalyzer - comprehensive coverage."""

from __future__ import annotations

import pytest

from chuk_virtual_expert_arithmetic.core.analyzer import TemplateAnalyzer


class TestTemplateAnalyzerInit:
    """Tests for TemplateAnalyzer initialization."""

    def test_init_creates_pattern_cache(self) -> None:
        """Test that initialization creates pattern cache."""
        analyzer = TemplateAnalyzer()
        assert len(analyzer._pattern_cache) == len(analyzer.SENTENCE_PATTERNS)

    def test_init_compiles_patterns(self) -> None:
        """Test that patterns are compiled as regex."""
        analyzer = TemplateAnalyzer()
        for _pattern_str, compiled in analyzer._pattern_cache.items():
            assert hasattr(compiled, "search")
            assert hasattr(compiled, "match")


class TestFingerprintScore:
    """Tests for fingerprint_score method."""

    @pytest.fixture
    def analyzer(self) -> TemplateAnalyzer:
        """Create analyzer instance."""
        return TemplateAnalyzer()

    def test_empty_queries_returns_zero(self, analyzer: TemplateAnalyzer) -> None:
        """Test that empty query list returns 0."""
        score = analyzer.fingerprint_score([])
        assert score == 0.0

    def test_uniform_queries_high_score(self, analyzer: TemplateAnalyzer) -> None:
        """Test that identical queries produce high score."""
        queries = ["How many apples does Alice have?"] * 10
        score = analyzer.fingerprint_score(queries)
        # Identical queries should be very templated
        assert score > 0.5

    def test_varied_queries_lower_score(self, analyzer: TemplateAnalyzer) -> None:
        """Test that varied queries produce lower score."""
        queries = [
            "How many apples does Alice have?",
            "What is the total cost of the groceries?",
            "Find the number of students in class.",
            "Calculate how much money Bob spent.",
            "Determine the total distance traveled.",
            "Figure out how many cookies were baked.",
            "If Jane has 5 books, how many pages total?",
            "There are 10 birds in the tree.",
            "John bought 3 pencils for school.",
            "Maria wants to save money for a trip.",
        ]
        score = analyzer.fingerprint_score(queries)
        # Varied queries should be less templated
        assert score < 0.8

    def test_score_is_between_zero_and_one(self, analyzer: TemplateAnalyzer) -> None:
        """Test that score is always between 0 and 1."""
        queries = ["Test query one.", "Test query two.", "Test query three."]
        score = analyzer.fingerprint_score(queries)
        assert 0.0 <= score <= 1.0


class TestAnalyze:
    """Tests for analyze method."""

    @pytest.fixture
    def analyzer(self) -> TemplateAnalyzer:
        """Create analyzer instance."""
        return TemplateAnalyzer()

    def test_empty_queries_returns_error(self, analyzer: TemplateAnalyzer) -> None:
        """Test that empty queries returns error dict."""
        result = analyzer.analyze([])
        assert "error" in result
        assert result["error"] == "No queries provided"

    def test_analyze_returns_expected_keys(self, analyzer: TemplateAnalyzer) -> None:
        """Test that analysis returns all expected keys."""
        queries = [
            "How many apples does Alice have?",
            "What is the total cost?",
        ]
        result = analyzer.analyze(queries)

        assert "count" in result
        assert "fingerprint_score" in result
        assert "length" in result
        assert "word_count" in result
        assert "sentence_count" in result
        assert "question_starters" in result
        assert "vocabulary" in result
        assert "uniformity" in result

    def test_analyze_count(self, analyzer: TemplateAnalyzer) -> None:
        """Test that count matches number of queries."""
        queries = ["Query 1.", "Query 2.", "Query 3."]
        result = analyzer.analyze(queries)
        assert result["count"] == 3

    def test_analyze_length_stats(self, analyzer: TemplateAnalyzer) -> None:
        """Test length statistics."""
        queries = ["Short.", "A medium query here.", "This is a longer query sentence."]
        result = analyzer.analyze(queries)

        assert "mean" in result["length"]
        assert "min" in result["length"]
        assert "max" in result["length"]
        assert "std" in result["length"]

        assert result["length"]["min"] == len("Short.")
        assert result["length"]["max"] == len("This is a longer query sentence.")

    def test_analyze_word_count_stats(self, analyzer: TemplateAnalyzer) -> None:
        """Test word count statistics."""
        queries = ["One two.", "One two three four.", "One two three four five six."]
        result = analyzer.analyze(queries)

        assert "mean" in result["word_count"]
        assert "min" in result["word_count"]
        assert "max" in result["word_count"]

        assert result["word_count"]["min"] == 2
        assert result["word_count"]["max"] == 6

    def test_analyze_sentence_count(self, analyzer: TemplateAnalyzer) -> None:
        """Test sentence count statistics."""
        queries = [
            "One sentence.",
            "First sentence. Second sentence.",
            "First. Second! Third?",
        ]
        result = analyzer.analyze(queries)

        assert "mean" in result["sentence_count"]
        assert "min" in result["sentence_count"]
        assert "max" in result["sentence_count"]

    def test_analyze_vocabulary_stats(self, analyzer: TemplateAnalyzer) -> None:
        """Test vocabulary analysis."""
        queries = ["Apple banana cherry.", "Apple date elderberry."]
        result = analyzer.analyze(queries)

        vocab = result["vocabulary"]
        assert "total_words" in vocab
        assert "unique_words" in vocab
        assert "richness" in vocab

        assert vocab["total_words"] == 6
        # unique words: apple, banana, cherry, date, elderberry = 5
        assert vocab["unique_words"] == 5
        assert 0.0 <= vocab["richness"] <= 1.0

    def test_analyze_uniformity_metrics(self, analyzer: TemplateAnalyzer) -> None:
        """Test uniformity metrics are included."""
        queries = ["How many apples?", "How many oranges?"]
        result = analyzer.analyze(queries)

        uniformity = result["uniformity"]
        assert "question_starter" in uniformity
        assert "sentence_pattern" in uniformity
        assert "ngram_repetition" in uniformity
        assert "length" in uniformity


class TestCompareToTarget:
    """Tests for compare_to_target method."""

    @pytest.fixture
    def analyzer(self) -> TemplateAnalyzer:
        """Create analyzer instance."""
        return TemplateAnalyzer()

    def test_default_target_metrics(self, analyzer: TemplateAnalyzer) -> None:
        """Test comparison with default GSM-8K metrics."""
        queries = ["How many apples does Alice have?", "What is the total cost?"]
        result = analyzer.compare_to_target(queries)

        assert "current" in result
        assert "target" in result
        assert "gaps" in result
        assert "recommendations" in result

    def test_custom_target_metrics(self, analyzer: TemplateAnalyzer) -> None:
        """Test comparison with custom target metrics."""
        queries = ["Test query one.", "Test query two."]
        custom_target = {
            "length_mean": 100,
            "word_count_mean": 20,
            "sentence_count_mean": 3,
            "vocab_richness": 0.5,
            "fingerprint_score": 0.1,
        }

        result = analyzer.compare_to_target(queries, custom_target)

        assert result["target"] == custom_target

    def test_gaps_calculation(self, analyzer: TemplateAnalyzer) -> None:
        """Test that gaps are calculated correctly."""
        queries = ["Short."]
        result = analyzer.compare_to_target(queries)

        # Length should be much shorter than GSM-8K's 180 mean
        assert result["gaps"]["length"] < 0


class TestQuestionStarterUniformity:
    """Tests for _question_starter_uniformity method."""

    @pytest.fixture
    def analyzer(self) -> TemplateAnalyzer:
        """Create analyzer instance."""
        return TemplateAnalyzer()

    def test_all_same_starter_high_uniformity(self, analyzer: TemplateAnalyzer) -> None:
        """Test that identical starters produce high uniformity."""
        queries = ["How many apples?", "How many oranges?", "How many bananas?"]
        uniformity = analyzer._question_starter_uniformity(queries)
        assert uniformity > 0.5

    def test_varied_starters_lower_uniformity(self, analyzer: TemplateAnalyzer) -> None:
        """Test that varied starters produce lower uniformity."""
        queries = [
            "How many apples?",
            "What is the total?",
            "Find the number.",
            "Calculate the sum.",
        ]
        uniformity = analyzer._question_starter_uniformity(queries)
        # Should be lower than all-same case
        assert uniformity < 1.0

    def test_no_starters_returns_zero(self, analyzer: TemplateAnalyzer) -> None:
        """Test that queries without starters return 0."""
        queries = ["Just a statement.", "Another statement.", "No questions here."]
        uniformity = analyzer._question_starter_uniformity(queries)
        assert uniformity == 0.0


class TestCountQuestionStarters:
    """Tests for _count_question_starters method."""

    @pytest.fixture
    def analyzer(self) -> TemplateAnalyzer:
        """Create analyzer instance."""
        return TemplateAnalyzer()

    def test_counts_starters_correctly(self, analyzer: TemplateAnalyzer) -> None:
        """Test that starters are counted correctly."""
        queries = [
            "How many apples?",
            "How many oranges?",
            "What is the total?",
            "How much does it cost?",
        ]
        counts = analyzer._count_question_starters(queries)

        assert counts["How many"] == 2
        assert counts["What is"] == 1
        assert counts["How much"] == 1

    def test_case_insensitive(self, analyzer: TemplateAnalyzer) -> None:
        """Test that counting is case insensitive."""
        queries = ["HOW MANY apples?", "how many oranges?"]
        counts = analyzer._count_question_starters(queries)
        assert counts["How many"] == 2

    def test_only_first_match_counted(self, analyzer: TemplateAnalyzer) -> None:
        """Test that only first matching starter is counted."""
        queries = ["How many things? What is the answer?"]
        counts = analyzer._count_question_starters(queries)
        # Should only count the first match
        total = sum(counts.values())
        assert total == 1


class TestSentencePatternOverlap:
    """Tests for _sentence_pattern_overlap method."""

    @pytest.fixture
    def analyzer(self) -> TemplateAnalyzer:
        """Create analyzer instance."""
        return TemplateAnalyzer()

    def test_matching_patterns(self, analyzer: TemplateAnalyzer) -> None:
        """Test queries matching patterns."""
        queries = [
            "Alice has 5 apples.",
            "Bob bought 3 oranges.",
            "There are 10 students.",
        ]
        overlap = analyzer._sentence_pattern_overlap(queries)
        # All should match patterns
        assert overlap > 0.5

    def test_no_matching_patterns(self, analyzer: TemplateAnalyzer) -> None:
        """Test queries not matching any pattern."""
        queries = [
            "The weather is nice today.",
            "Mathematics is interesting.",
            "Coffee tastes good in the morning.",
        ]
        overlap = analyzer._sentence_pattern_overlap(queries)
        assert overlap == 0.0

    def test_empty_queries(self, analyzer: TemplateAnalyzer) -> None:
        """Test empty query list."""
        overlap = analyzer._sentence_pattern_overlap([])
        assert overlap == 0.0


class TestNgramRepetition:
    """Tests for _ngram_repetition method."""

    @pytest.fixture
    def analyzer(self) -> TemplateAnalyzer:
        """Create analyzer instance."""
        return TemplateAnalyzer()

    def test_high_repetition(self, analyzer: TemplateAnalyzer) -> None:
        """Test queries with repeated n-grams."""
        queries = [
            "The big red apple is here.",
            "The big red orange is there.",
            "The big red banana is good.",
        ]
        repetition = analyzer._ngram_repetition(queries, n=3)
        # "the big red" appears multiple times
        assert repetition > 0.0

    def test_no_repetition(self, analyzer: TemplateAnalyzer) -> None:
        """Test queries with no repeated n-grams."""
        queries = [
            "One two three four five.",
            "Six seven eight nine ten.",
            "Eleven twelve thirteen fourteen.",
        ]
        repetition = analyzer._ngram_repetition(queries, n=3)
        assert repetition == 0.0

    def test_short_queries(self, analyzer: TemplateAnalyzer) -> None:
        """Test queries shorter than n-gram size."""
        queries = ["Hi.", "Hey."]
        repetition = analyzer._ngram_repetition(queries, n=3)
        assert repetition == 0.0

    def test_empty_queries(self, analyzer: TemplateAnalyzer) -> None:
        """Test empty query list."""
        repetition = analyzer._ngram_repetition([], n=3)
        assert repetition == 0.0


class TestLengthUniformity:
    """Tests for _length_uniformity method."""

    @pytest.fixture
    def analyzer(self) -> TemplateAnalyzer:
        """Create analyzer instance."""
        return TemplateAnalyzer()

    def test_identical_lengths_high_uniformity(self, analyzer: TemplateAnalyzer) -> None:
        """Test that identical lengths produce high uniformity."""
        queries = ["AAAA", "BBBB", "CCCC"]  # All length 4
        uniformity = analyzer._length_uniformity(queries)
        assert uniformity == 1.0

    def test_varied_lengths_lower_uniformity(self, analyzer: TemplateAnalyzer) -> None:
        """Test that varied lengths produce lower uniformity."""
        queries = ["A", "BB", "CCCCCCCCCCCCCCCCCCCC"]
        uniformity = analyzer._length_uniformity(queries)
        assert uniformity < 1.0

    def test_empty_queries(self, analyzer: TemplateAnalyzer) -> None:
        """Test empty query list."""
        uniformity = analyzer._length_uniformity([])
        assert uniformity == 0.0

    def test_empty_strings(self, analyzer: TemplateAnalyzer) -> None:
        """Test queries that are all empty strings."""
        queries = ["", "", ""]
        uniformity = analyzer._length_uniformity(queries)
        assert uniformity == 0.0  # Mean is 0, so returns 0


class TestStd:
    """Tests for _std method."""

    @pytest.fixture
    def analyzer(self) -> TemplateAnalyzer:
        """Create analyzer instance."""
        return TemplateAnalyzer()

    def test_single_value(self, analyzer: TemplateAnalyzer) -> None:
        """Test with single value returns 0."""
        std = analyzer._std([5])
        assert std == 0.0

    def test_empty_list(self, analyzer: TemplateAnalyzer) -> None:
        """Test with empty list returns 0."""
        std = analyzer._std([])
        assert std == 0.0

    def test_identical_values(self, analyzer: TemplateAnalyzer) -> None:
        """Test with identical values returns 0."""
        std = analyzer._std([5, 5, 5, 5])
        assert std == 0.0

    def test_known_values(self, analyzer: TemplateAnalyzer) -> None:
        """Test with known values."""
        # std of [2, 4, 4, 4, 5, 5, 7, 9] = 2.0 (population std)
        values = [2, 4, 4, 4, 5, 5, 7, 9]
        std = analyzer._std(values)
        assert abs(std - 2.0) < 0.01


class TestGenerateRecommendations:
    """Tests for _generate_recommendations method."""

    @pytest.fixture
    def analyzer(self) -> TemplateAnalyzer:
        """Create analyzer instance."""
        return TemplateAnalyzer()

    def test_short_queries_recommendation(self, analyzer: TemplateAnalyzer) -> None:
        """Test recommendation for short queries."""
        current = {"length": {"mean": 50}, "fingerprint_score": 0.1, "vocabulary": {"richness": 0.4}, "sentence_count": {"mean": 4}}
        target = {"length_mean": 180, "fingerprint_score": 0.15, "vocab_richness": 0.35, "sentence_count_mean": 4}

        recs = analyzer._generate_recommendations(current, target)
        assert any("too short" in r.lower() for r in recs)

    def test_templated_queries_recommendation(self, analyzer: TemplateAnalyzer) -> None:
        """Test recommendation for templated queries."""
        current = {"length": {"mean": 180}, "fingerprint_score": 0.5, "vocabulary": {"richness": 0.4}, "sentence_count": {"mean": 4}}
        target = {"length_mean": 180, "fingerprint_score": 0.15, "vocab_richness": 0.35, "sentence_count_mean": 4}

        recs = analyzer._generate_recommendations(current, target)
        assert any("templated" in r.lower() for r in recs)

    def test_limited_vocab_recommendation(self, analyzer: TemplateAnalyzer) -> None:
        """Test recommendation for limited vocabulary."""
        current = {"length": {"mean": 180}, "fingerprint_score": 0.1, "vocabulary": {"richness": 0.1}, "sentence_count": {"mean": 4}}
        target = {"length_mean": 180, "fingerprint_score": 0.15, "vocab_richness": 0.35, "sentence_count_mean": 4}

        recs = analyzer._generate_recommendations(current, target)
        assert any("vocabulary" in r.lower() for r in recs)

    def test_few_sentences_recommendation(self, analyzer: TemplateAnalyzer) -> None:
        """Test recommendation for too few sentences."""
        current = {"length": {"mean": 180}, "fingerprint_score": 0.1, "vocabulary": {"richness": 0.4}, "sentence_count": {"mean": 1}}
        target = {"length_mean": 180, "fingerprint_score": 0.15, "vocab_richness": 0.35, "sentence_count_mean": 4}

        recs = analyzer._generate_recommendations(current, target)
        assert any("sentences" in r.lower() for r in recs)

    def test_well_balanced_recommendation(self, analyzer: TemplateAnalyzer) -> None:
        """Test recommendation for well-balanced queries."""
        current = {"length": {"mean": 180}, "fingerprint_score": 0.1, "vocabulary": {"richness": 0.4}, "sentence_count": {"mean": 4}}
        target = {"length_mean": 180, "fingerprint_score": 0.15, "vocab_richness": 0.35, "sentence_count_mean": 4}

        recs = analyzer._generate_recommendations(current, target)
        assert any("well-balanced" in r.lower() for r in recs)
