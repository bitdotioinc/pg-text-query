import unittest
from unittest.mock import Mock, patch

from pg_text_query.gen_query import generate_query, DEFAULT_COMPLETION_CONFIG
from pg_text_query.errors import QueryGenError


class QueryGenTestCase(unittest.TestCase):

    @patch("openai.Completion.create")
    @patch("pg_text_query.gen_query.openai.api_key")
    def test_generate_query_invalid_syntax(
        self,
        mock_openai_key: Mock,
        mock_completion_create: Mock,
    ) -> None:
        prompt = "\n".join(
            [
                "-- Language PostgreSQL",
                "-- Table penguins, columns = [bill_length_mm double precision, bill_depth_mm double precision, flipper_length_mm bigint, body_mass_g bigint, year bigint, species text, island text, sex text]",
                "-- A PostgreSQL query to return 1 and a PostgreSQL query for how many penguin records are there?",
                "SELECT 1;",
            ]
        )
        # Demonstrate default override
        expected_kwargs = {**DEFAULT_COMPLETION_CONFIG}
        mock_completion_create.return_value = {"choices": [{"text": "sum(records)"}]}
        mock_openai_key.return_value.api_key.return_value = "FAKE_KEY"
        
        with self.assertRaises(QueryGenError) as ctx:
            _ = generate_query(prompt, validate_sql=True)
        self.assertIn("Generated query is empty, only a comment, or invalid.", str(ctx.exception))
        mock_completion_create.assert_called_once_with(
            prompt=prompt,
            **expected_kwargs,
        )

    @patch("openai.Completion.create")
    @patch("pg_text_query.gen_query.openai.api_key")
    def test_generate_query_returns_only_comment(
        self,
        mock_openai_key: Mock,
        mock_completion_create: Mock,
    ) -> None:
        prompt = "\n".join(
            [
                "-- Language PostgreSQL",
                "-- Table penguins, columns = [bill_length_mm double precision, bill_depth_mm double precision, flipper_length_mm bigint, body_mass_g bigint, year bigint, species text, island text, sex text]",
                "-- A PostgreSQL query to return 1 and a PostgreSQL query for how many penguin records are there?",
                "SELECT 1;",
            ]
        )
        # Demonstrate default override
        expected_kwargs = {**DEFAULT_COMPLETION_CONFIG}
        mock_completion_create.return_value = {"choices": [{"text": "-- SELECT COUNT(*) FROM penguins"}]}
        mock_openai_key.return_value.api_key.return_value = "FAKE_KEY"
        
        with self.assertRaises(QueryGenError) as ctx:
            _ = generate_query(prompt, validate_sql=True)
        self.assertIn("Generated query is empty, only a comment, or invalid.", str(ctx.exception))
        mock_completion_create.assert_called_once_with(
            prompt=prompt,
            **expected_kwargs,
        )

    @patch("openai.Completion.create")
    @patch("pg_text_query.gen_query.openai.api_key")
    def test_generate_query_w_param(
        self,
        mock_openai_key: Mock,
        mock_completion_create: Mock,
    ) -> None:
        prompt = "\n".join(
            [
                "-- Language PostgreSQL",
                "-- Table penguins, columns = [bill_length_mm double precision, bill_depth_mm double precision, flipper_length_mm bigint, body_mass_g bigint, year bigint, species text, island text, sex text]",
                "-- A PostgreSQL query to return 1 and a PostgreSQL query for how many penguins are there?",
                "SELECT 1;",
            ]
        )
        expected_query = "SELECT COUNT(*)"
        # Demonstrate default override
        expected_kwargs = {**DEFAULT_COMPLETION_CONFIG, **{"temperature": 0.5}}
        mock_completion_create.return_value = {"choices": [{"text": "SELECT COUNT(*)"}]}
        mock_openai_key.return_value.api_key.return_value = "FAKE_KEY"
        query = generate_query(prompt, temperature=0.5)
        self.assertEqual(query, expected_query)
        mock_completion_create.assert_called_once_with(
            prompt=prompt,
            **expected_kwargs,
        )
