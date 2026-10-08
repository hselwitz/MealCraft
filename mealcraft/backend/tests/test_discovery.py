"""Discovery stays independent of meal plans and learns from cooking feedback."""
import unittest
from pydantic import ValidationError
from unittest.mock import patch
import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.db import Base, get_db
from app.models.recipe import Recipe
from app.models.repertoire import RepertoireMeal, FAMILIAR_MEALS
from app.models.settings import AppSettings
from app.routers.discovery import router
from app.routers.recipes import router as recipes_router
from app.llm.client import get_llm_client, LLMClient
from app.llm.schemas import RecipeOutput
from app.schemas.discovery import DinnerIdeas, DiscoveryRequest

IDEA = {"title": "Chili chicken with lime", "description": "Bone-in chicken breast with rice and frozen peppers.",
        "familiar_connection": "Your usual chicken bowl with a different sauce.", "active_time_min": 10,
        "total_time_min": 55, "cleanup": "Roasting pan + rice pot", "extra_ingredients": ["lime"],
        "convenience_tip": "Use frozen peppers straight from the freezer."}
RECIPE = {"title": IDEA["title"], "description": IDEA["description"], "prep_time_min": 5,
          "cook_time_min": 50, "total_time_min": 55, "difficulty": "easy", "servings": 2,
          "ingredients": [{"ingredient_name": "chicken breast", "quantity": 2, "unit": "pieces", "prep_note": "skin-on, bone-in"}],
          "steps": [{"step_number": 1, "instruction": "Season the bone-in chicken.", "duration_min": 5, "is_active": True},
                    {"step_number": 2, "instruction": "Roast until cooked through.", "duration_min": 50, "is_active": False}]}


class FakeLLM:
    def __init__(self):
        self.context = None
        self.constraints = None
        self.output = RecipeOutput.model_validate(RECIPE)
    async def suggest_dinners(self, request, context, settings, selected):
        self.context = (request, context, settings, selected)
        return DinnerIdeas.model_validate({"ideas": [{**IDEA, "title": IDEA["title"] + str(i)} for i in range(3)]})
    async def generate_recipe(self, concept, constraints):
        self.constraints = constraints
        return self.output
    async def canonicalize_ingredient(self, name, existing):
        return name.lower()


class DiscoveryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.sessions() as session:
            session.add_all(RepertoireMeal(**meal, familiar=True) for meal in FAMILIAR_MEALS)
            session.add(AppSettings(id="default", data={"openRouterApiKey": "never-send-to-model", "dietaryRestrictions": ["no dairy"], "defaultServings": 1}))
            await session.commit()
        async def database():
            async with self.sessions() as session:
                yield session
                await session.commit()
        self.llm = FakeLLM()
        async def llm():
            yield self.llm
        app = FastAPI()
        app.include_router(router, prefix="/api")
        app.include_router(recipes_router, prefix="/api")
        app.dependency_overrides[get_db] = database
        app.dependency_overrides[get_llm_client] = llm
        self.http = TestClient(app)

    async def asyncTearDown(self):
        self.http.close()
        await self.engine.dispose()

    async def test_three_usual_meals_available_without_a_plan(self):
        response = self.http.get("/api/repertoire")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)
        self.assertIn("bone-in", next(m["notes"] for m in response.json() if m["id"] == "usual-chicken"))

    async def test_discovery_uses_profile_but_does_not_generate_recipes(self):
        response = self.http.post("/api/discover/ideas", json={"request": "Chicken and rice", "familiar_meal_id": "usual-chicken"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["ideas"]), 3)
        request, context, prefs, selected = self.llm.context
        self.assertEqual(request.direction, "twist")
        self.assertEqual(selected.id, "usual-chicken")
        self.assertEqual(prefs["dietaryRestrictions"], ["no dairy"])
        self.assertNotIn("openRouterApiKey", prefs)
        async with self.sessions() as session:
            self.assertEqual(await session.scalar(select(func.count()).select_from(Recipe)), 0)

    async def test_selected_idea_generates_complete_recipe_using_settings(self):
        response = self.http.post("/api/discover/recipe", json={"idea": IDEA, "max_active_min": 10, "request": "Keep the bone-in chicken"})
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["active_time_min"], 5)
        self.assertEqual(len(data["steps"]), 2)
        self.assertEqual(data["recipe_ingredients"][0]["prep_note"], "skin-on, bone-in")
        self.assertEqual(self.llm.constraints["target_servings"], 1)
        self.assertEqual(self.llm.constraints["cooking_mode"], "dinner")
        self.assertEqual(self.llm.constraints["dietary_restrictions"], ["no dairy"])
        self.assertEqual(self.http.get("/api/recipes/" + data["id"]).status_code, 200)
        self.assertEqual(self.http.get("/api/recipes").json()[0]["total_time_min"], 55)

    async def test_over_budget_recipe_is_not_saved(self):
        self.llm.output.steps[0].duration_min = 30
        response = self.http.post("/api/discover/recipe", json={"idea": IDEA, "max_active_min": 10})
        self.assertEqual(response.status_code, 502)
        async with self.sessions() as session:
            self.assertEqual(await session.scalar(select(func.count()).select_from(Recipe)), 0)

    async def test_incomplete_recipe_is_not_saved(self):
        self.llm.output.ingredients = []
        response = self.http.post("/api/discover/recipe", json={"idea": IDEA})
        self.assertEqual(response.status_code, 502)

    async def test_save_cooking_feedback_and_notes_influence_next_ideas(self):
        recipe = self.http.post("/api/discover/recipe", json={"idea": IDEA}).json()
        response = self.http.put(f'/api/repertoire/recipes/{recipe["id"]}', json={"saved": True, "cooked": True, "verdict": "again", "easy_enough": False, "notes": "Use frozen vegetables"})
        self.assertEqual(response.status_code, 200, response.text)
        meal = response.json()
        self.assertEqual(meal["cooked_count"], 1)
        self.assertTrue(meal["last_cooked_at"])
        self.http.post("/api/discover/ideas", json={})
        context = self.llm.context[1]
        remembered = next(m for m in context if m["recipe_id"] == recipe["id"])
        self.assertFalse(remembered["easy_enough"])
        self.assertEqual(remembered["verdict"], "again")
        self.assertEqual(remembered["notes"], "Use frozen vegetables")
        self.http.put(f'/api/repertoire/recipes/{recipe["id"]}', json={"saved": False})
        self.assertEqual(len(self.http.get("/api/repertoire").json()), 4)
        self.assertEqual(self.http.delete(f'/api/recipes/{recipe["id"]}').status_code, 204)
        self.assertEqual(len(self.http.get("/api/repertoire").json()), 3)

    async def test_custom_meal_needs_no_recipe(self):
        response = self.http.post("/api/repertoire", json={"title": "My rice bowl", "notes": "Microwave rice and frozen vegetables"})
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.json()["recipe_id"])
        self.assertTrue(response.json()["familiar"])
        self.assertEqual(self.http.post("/api/repertoire", json={"title": "   "}).status_code, 422)

    async def test_invalid_selection_and_limits(self):
        self.assertEqual(self.http.post("/api/discover/ideas", json={"familiar_meal_id": "missing"}).status_code, 404)
        self.assertEqual(self.http.post("/api/discover/ideas", json={"max_active_min": 0}).status_code, 422)
        self.assertEqual(self.http.put("/api/repertoire/recipes/missing", json={"saved": True}).status_code, 404)


class PromptTests(unittest.IsolatedAsyncioTestCase):
    def test_repeated_ideas_are_rejected(self):
        with self.assertRaises(ValidationError):
            DinnerIdeas.model_validate({"ideas": [IDEA, IDEA, IDEA]})

    def test_elapsed_time_cannot_be_shorter_than_active_time(self):
        with self.assertRaises(ValidationError):
            DinnerIdeas.model_validate({"ideas": [{**IDEA, "title": f"Dinner {i}", "total_time_min": 5} for i in range(3)]})

    async def test_discovery_prompt_preserves_convenience_and_real_cook_times(self):
        client = LLMClient("test-key", "provider/model")
        await client._client.aclose()
        def handle(request):
            import json
            payload = json.loads(request.content)
            prompt = payload["messages"][0]["content"]
            self.assertIn("Bone-in chicken", prompt)
            self.assertIn("at most 15 minutes", prompt)
            self.assertIn("easy_enough=false", prompt)
            self.assertEqual(payload["tools"][0]["function"]["name"], "suggest_dinners")
            data = {"ideas": [{**IDEA, "title": f"Dinner {i}"} for i in range(3)]}
            return httpx.Response(200, json={"choices": [{"message": {"tool_calls": [{"function": {"name": "suggest_dinners", "arguments": json.dumps(data)}}]}}]})
        client._client = httpx.AsyncClient(base_url="https://openrouter.ai/api/v1/", transport=httpx.MockTransport(handle))
        try:
            ideas = await client.suggest_dinners(DiscoveryRequest(), [], {}, None)
            self.assertEqual(len(ideas.ideas), 3)
        finally:
            await client._client.aclose()
