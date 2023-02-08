"""Example of the db_schema format generated in db_schema.py and expected in prompt.py"""

example_db_schema = {
    "description": "# Palmer\xa0Archipelago (Antarctica) penguin data\n"
    "\n"
    "\n"
    ">\xa0The goal of palmerpenguins is to provide a great dataset "
    "for data exploration & visualization, as an alternative to "
    "`iris`.\n"
    "\n"
    "\n"
    "\\- "
    "[source](https://github.com/allisonhorst/palmerpenguins/)\n"
    "\n"
    "\n"
    "\n"
    "Source:\n"
    "Horst AM, Hill AP, Gorman KB (2020). palmerpenguins: "
    "Palmer\xa0Archipelago (Antarctica) penguin data. R package "
    "version 0.1.0.\xa0"
    "https://allisonhorst.github.io/palmerpenguins/\n"
    "\n"
    "\n"
    "Data originally published:\xa0Gorman KB, Williams TD, Fraser "
    "WR (2014). Ecological sexual dimorphism and environmental "
    "variability within a community of Antarctic penguins (genus "
    "Pygoscelis). PLoS ONE 9(3):e90081. "
    "https://doi.org/10.1371/journal.pone.0090081",
    "name": "bitdotio/palmerpenguins",
    "schemata": [
        {
            "description": "standard public schema",
            "is_foreign": False,
            "name": "public",
            "tables": [
                {
                    "columns": [
                        {
                            "character_maximum_length": None,
                            "column_default": None,
                            "data_type": "text",
                            "description": "penguin species "
                            "(Adélie, Chinstrap, "
                            "or\xa0Gentoo)",
                            "is_nullable": "YES",
                            "name": "species",
                            "ordinal_position": 2,
                        },
                        {
                            "character_maximum_length": None,
                            "column_default": None,
                            "data_type": "text",
                            "description": "island in Paler "
                            "archipelago (Biscoe, "
                            "Dream, or Torgersen)",
                            "is_nullable": "YES",
                            "name": "island",
                            "ordinal_position": 3,
                        },
                        {
                            "character_maximum_length": None,
                            "column_default": None,
                            "data_type": "double precision",
                            "description": "penguin bill length " "(mm)",
                            "is_nullable": "YES",
                            "name": "bill_length_mm",
                            "ordinal_position": 4,
                        },
                        {
                            "character_maximum_length": None,
                            "column_default": None,
                            "data_type": "double precision",
                            "description": "penguin bill depth " "(mm)",
                            "is_nullable": "YES",
                            "name": "bill_depth_mm",
                            "ordinal_position": 5,
                        },
                        {
                            "character_maximum_length": None,
                            "column_default": None,
                            "data_type": "bigint",
                            "description": "penguin flipper length " "(mm)",
                            "is_nullable": "YES",
                            "name": "flipper_length_mm",
                            "ordinal_position": 6,
                        },
                        {
                            "character_maximum_length": None,
                            "column_default": None,
                            "data_type": "bigint",
                            "description": "penguin body mass (g)",
                            "is_nullable": "YES",
                            "name": "body_mass_g",
                            "ordinal_position": 7,
                        },
                        {
                            "character_maximum_length": None,
                            "column_default": None,
                            "data_type": "text",
                            "description": "sex of penguin (male, " "female)",
                            "is_nullable": "YES",
                            "name": "sex",
                            "ordinal_position": 8,
                        },
                        {
                            "character_maximum_length": None,
                            "column_default": None,
                            "data_type": "bigint",
                            "description": "study year (2007, " "2008, or 2007)",
                            "is_nullable": "YES",
                            "name": "year",
                            "ordinal_position": 9,
                        },
                    ],
                    "description": "Measurements of 344 penguins of "
                    "three different species from three "
                    "islands in the Palmer archipelago.",
                    "name": "penguins",
                }
            ],
            "views": [],
        }
    ],
}
