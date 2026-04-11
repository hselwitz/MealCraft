"""Tool use schema definitions for Anthropic API."""

CREATE_WEEKLY_PLAN_TOOL = {
    "name": "create_weekly_plan",
    "description": (
        "Generate a batch-cooking weekly meal plan. One slot is the batch prep session (is_assembly=false) "
        "where all base components are cooked. All other slots that draw from batch components must have "
        "is_assembly=true, estimated_cook_min of 0–5, and a batch_component referencing what was prepped."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "meal_slots": {
                "type": "array",
                "description": "List of meal slots for the week",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                        "meal_type": {
                            "type": "string",
                            "enum": ["breakfast", "lunch", "dinner", "snack"],
                        },
                        "meal_concept": {
                            "type": "string",
                            "description": "Specific dish name/concept",
                        },
                        "estimated_prep_min": {
                            "type": "integer",
                            "description": "Estimated active prep time in minutes",
                        },
                        "estimated_cook_min": {
                            "type": "integer",
                            "description": "Estimated cook time in minutes",
                        },
                        "batch_component": {
                            "type": "string",
                            "description": "Pre-cooked batch component(s) this meal assembles from (e.g. 'roasted chicken thighs, brown rice'). Required when is_assembly is true.",
                            "nullable": True,
                        },
                        "is_assembly": {
                            "type": "boolean",
                            "description": "True if this meal only assembles from pre-cooked batch components (no cooking from raw). False for the batch prep session itself.",
                        },
                    },
                    "required": [
                        "date",
                        "meal_type",
                        "meal_concept",
                        "estimated_prep_min",
                        "estimated_cook_min",
                        "is_assembly",
                    ],
                },
            },
            "batch_components": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ingredients/components prepared in batch that span multiple meals",
            },
            "estimated_total_active_min": {
                "type": "integer",
                "description": "Total active cooking minutes for the week",
            },
            "notes": {
                "type": "string",
                "description": "Notes about the plan, ingredient overlaps, time-saving tips",
            },
        },
        "required": ["meal_slots", "batch_components", "estimated_total_active_min", "notes"],
    },
}

GENERATE_RECIPE_TOOL = {
    "name": "generate_recipe",
    "description": (
        "Generate a complete recipe with all ingredients, steps, and nutritional information. "
        "Provide detailed, actionable instructions with time estimates for each step."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {
                "type": "string",
                "description": "2-3 sentence description of the dish",
            },
            "prep_time_min": {"type": "integer"},
            "cook_time_min": {"type": "integer"},
            "total_time_min": {"type": "integer"},
            "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
            "servings": {"type": "number"},
            "calories_per_serving": {"type": "integer", "nullable": True},
            "protein_g": {"type": "number", "nullable": True},
            "carbs_g": {"type": "number", "nullable": True},
            "fat_g": {"type": "number", "nullable": True},
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags like vegetarian, gluten-free, quick, batch-friendly",
            },
            "ingredients": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ingredient_name": {
                            "type": "string",
                            "description": "Canonical ingredient name",
                        },
                        "quantity": {"type": "number"},
                        "unit": {"type": "string"},
                        "prep_note": {
                            "type": "string",
                            "nullable": True,
                            "description": "e.g. diced, minced",
                        },
                        "is_optional": {"type": "boolean"},
                    },
                    "required": ["ingredient_name", "quantity", "unit", "is_optional"],
                },
            },
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "step_number": {"type": "integer"},
                        "instruction": {
                            "type": "string",
                            "description": "Detailed, actionable step",
                        },
                        "duration_min": {"type": "integer", "nullable": True},
                        "is_active": {
                            "type": "boolean",
                            "description": "True if requires active attention",
                        },
                    },
                    "required": ["step_number", "instruction", "is_active"],
                },
            },
        },
        "required": [
            "title",
            "description",
            "prep_time_min",
            "cook_time_min",
            "total_time_min",
            "difficulty",
            "servings",
            "tags",
            "ingredients",
            "steps",
        ],
    },
}

OPTIMIZE_PREP_PLAN_TOOL = {
    "name": "optimize_prep_plan",
    "description": (
        "Create an optimized prep plan for cooking multiple recipes efficiently. "
        "Group tasks into sessions and identify opportunities for batch cooking and parallel work."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "task_name": {"type": "string"},
                        "duration_min": {"type": "integer"},
                        "is_active": {"type": "boolean"},
                        "batch_group": {"type": "string", "nullable": True},
                        "depends_on": {"type": "array", "items": {"type": "string"}},
                        "tip": {"type": "string", "nullable": True, "description": "A short, practical tip for this step — only include if genuinely non-obvious (e.g. technique, temperature, common mistake). Omit for self-explanatory tasks."},
                    },
                    "required": ["task_name", "duration_min", "is_active", "depends_on"],
                },
            },
            "total_active_min": {"type": "integer"},
            "total_passive_min": {"type": "integer"},
            "recommended_sessions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "e.g. ['Sunday 2h batch prep', 'Wednesday 30min dinner prep']",
            },
        },
        "required": ["tasks", "total_active_min", "total_passive_min", "recommended_sessions"],
    },
}

GENERATE_GROCERY_LIST_TOOL = {
    "name": "generate_grocery_list",
    "description": (
        "Generate a consolidated grocery list from recipe ingredients. "
        "Combine similar items, adjust for purchasable quantities, and organize by store section."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ingredient_name": {"type": "string"},
                        "quantity": {"type": "number"},
                        "unit": {"type": "string"},
                        "store_section": {
                            "type": "string",
                            "enum": [
                                "produce",
                                "meat",
                                "dairy",
                                "bakery",
                                "pantry",
                                "frozen",
                                "other",
                            ],
                        },
                        "notes": {"type": "string", "nullable": True},
                    },
                    "required": ["ingredient_name", "quantity", "unit", "store_section"],
                },
            }
        },
        "required": ["items"],
    },
}

SUGGEST_LEFTOVER_USE_TOOL = {
    "name": "suggest_leftover_use",
    "description": (
        "Suggest creative ways to use available leftovers in upcoming meal slots. "
        "Consider expiry dates and flavor combinations."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "suggestions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Concrete suggestions for using leftovers",
            }
        },
        "required": ["suggestions"],
    },
}
