import unittest

from pg_text_query.prompt import get_default_prompt


test_db_schema = {
    "name": "bitdotio/palmerpenguins",
    "schemata": [
        {
            "name": "public",
            "views": [],
            "tables": [
                {
                    "name": "penguins",
                    "columns": [
                        {
                            "name": "bill_length_mm",
                            "data_type": "double precision",
                            "description": "penguin bill length (mm)",
                            "is_nullable": "YES",
                            "column_default": None,
                            "ordinal_position": 4,
                            "character_maximum_length": None,
                        },
                        {
                            "name": "bill_depth_mm",
                            "data_type": "double precision",
                            "description": "penguin bill depth (mm)",
                            "is_nullable": "YES",
                            "column_default": None,
                            "ordinal_position": 5,
                            "character_maximum_length": None,
                        },
                        {
                            "name": "flipper_length_mm",
                            "data_type": "bigint",
                            "description": "penguin flipper length (mm)",
                            "is_nullable": "YES",
                            "column_default": None,
                            "ordinal_position": 6,
                            "character_maximum_length": None,
                        },
                        {
                            "name": "body_mass_g",
                            "data_type": "bigint",
                            "description": "penguin body mass (g)",
                            "is_nullable": "YES",
                            "column_default": None,
                            "ordinal_position": 7,
                            "character_maximum_length": None,
                        },
                        {
                            "name": "year",
                            "data_type": "bigint",
                            "description": "study year (2007, 2008, or 2007)",
                            "is_nullable": "YES",
                            "column_default": None,
                            "ordinal_position": 9,
                            "character_maximum_length": None,
                        },
                        {
                            "name": "species",
                            "data_type": "text",
                            "description": "penguin species (Adélie, Chinstrap, or\xa0Gentoo)",
                            "is_nullable": "YES",
                            "column_default": None,
                            "ordinal_position": 2,
                            "character_maximum_length": None,
                        },
                        {
                            "name": "island",
                            "data_type": "text",
                            "description": "island in Paler archipelago (Biscoe, Dream, or Torgersen)",
                            "is_nullable": "YES",
                            "column_default": None,
                            "ordinal_position": 3,
                            "character_maximum_length": None,
                        },
                        {
                            "name": "sex",
                            "data_type": "text",
                            "description": "sex of penguin (male, female)",
                            "is_nullable": "YES",
                            "column_default": None,
                            "ordinal_position": 8,
                            "character_maximum_length": None,
                        },
                    ],
                    "description": "Measurements of 344 penguins of three different species from three islands in the Palmer archipelago.",
                }
            ],
            "description": "standard public schema",
        }
    ],
    "description": "# Palmer\xa0Archipelago (Antarctica) penguin data\n\n\n>\xa0The goal of palmerpenguins is to provide a great dataset.",
}


class PromptTestCase(unittest.TestCase):
    def test_get_prompt(self) -> None:
        expected = "\n".join(
            [
                "-- Language PostgreSQL",
                "-- Table = \"penguins\", columns = [bill_length_mm double precision, bill_depth_mm double precision, flipper_length_mm bigint, body_mass_g bigint, year bigint, species text, island text, sex text]",
                "-- A PostgreSQL query to return 1 and a PostgreSQL query for how many penguins are there?",
                "SELECT 1;",
            ]
        )

        prompt = get_default_prompt("how many penguins are there?", test_db_schema)
        self.assertEqual(prompt, expected)
