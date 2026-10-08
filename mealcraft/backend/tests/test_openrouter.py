"""Run with: python -m unittest discover -s tests -v (from backend)."""
import json
import unittest
from unittest.mock import patch

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.db import Base, get_db
from app.llm.client import LLMClient, _extract_tool_input, get_llm_client
from app.routers.settings import router
from app.routers.recipes import router as recipes_router

RECIPE = {
    "title": "New dinner", "description": "A quick dinner", "prep_time_min": 5,
    "cook_time_min": 10, "total_time_min": 15, "difficulty": "easy", "servings": 2,
    "ingredients": [], "steps": [],
}


def completion(name, data, finish_reason="tool_calls"):
    return {"choices": [{"finish_reason": finish_reason, "message": {"tool_calls": [{
        "function": {"name": name, "arguments": json.dumps(data)}
    }]}}]}


class OpenRouterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = LLMClient("test-secret", "anthropic/claude-sonnet-4")
        await self.client._client.aclose()

    async def asyncTearDown(self):
        await self.client._client.aclose()

    def transport(self, handler):
        self.client._client = httpx.AsyncClient(
            base_url="https://openrouter.ai/api/v1/",
            headers={"Authorization": "Bearer test-secret"},
            transport=httpx.MockTransport(handler),
        )

    async def test_all_generation_tasks_use_openrouter_tools(self):
        outputs = {
            "generate_recipe": RECIPE,
            "create_weekly_plan": {"meal_slots": [], "estimated_total_active_min": 0, "notes": ""},
            "optimize_prep_plan": {"tasks": [], "total_active_min": 0, "total_passive_min": 0},
            "generate_grocery_list": {"items": []},
            "suggest_leftover_use": {"suggestions": ["Try a new sauce"]},
        }
        seen = []
        def handle(request):
            self.assertEqual(str(request.url), "https://openrouter.ai/api/v1/chat/completions")
            self.assertEqual(request.headers["Authorization"], "Bearer test-secret")
            payload = json.loads(request.content)
            self.assertEqual(payload["model"], self.client.model)
            self.assertTrue(payload["provider"]["require_parameters"])
            tool = payload["tools"][0]
            self.assertEqual(tool["type"], "function")
            self.assertIn("parameters", tool["function"])
            name = tool["function"]["name"]
            self.assertEqual(payload["tool_choice"], "auto")
            seen.append(name)
            return httpx.Response(200, json=completion(name, outputs[name]))
        self.transport(handle)
        await self.client.generate_recipe("Dinner", {})
        assembly = await self.client.generate_assembly_recipe("Bowl", {}, ["rice"])
        self.assertIn("batch-assembly", assembly.tags)
        await self.client.generate_weekly_plan({}, {}, [], [])
        await self.client.optimize_prep_plan(["rice"], 2, "2026-10-08", "2026-10-10")
        await self.client.generate_grocery_list([], [], [])
        await self.client.suggest_leftover_use([], [])
        self.assertEqual(len(seen), 6)

    async def test_stream_handles_fragmented_tool_arguments(self):
        arguments = json.dumps(RECIPE)
        frames = [{"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {
            "name": "generate_recipe", "arguments": arguments[:15]}}]}}]},
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {
                "arguments": arguments[15:]}}]}, "finish_reason": "tool_calls"}]}]
        body = ": heartbeat\n\n" + "".join("data: " + json.dumps(frame) + "\n\n" for frame in frames) + "data: [DONE]\n\n"
        def handle(request):
            self.assertTrue(json.loads(request.content)["stream"])
            return httpx.Response(200, text=body)
        self.transport(handle)
        events = [json.loads(e[6:].strip()) async for e in self.client.generate_recipe_stream("Dinner", {})]
        self.assertEqual(events[-1]["recipe"]["title"], RECIPE["title"])
        self.assertEqual("".join(e.get("partial", "") for e in events), arguments)

    async def test_model_rejecting_forced_tool_selection_can_generate(self):
        def handle(request):
            payload = json.loads(request.content)
            if payload["tool_choice"] != "auto":
                return httpx.Response(404, json={"error": {
                    "message": "No endpoints found that support the provided tool_choice value."}})
            return httpx.Response(200, json=completion("generate_recipe", RECIPE))
        self.transport(handle)
        recipe = await self.client.generate_recipe("Dinner", {})
        self.assertEqual(recipe.title, RECIPE["title"])

    async def test_provider_errors_do_not_echo_response_body(self):
        self.transport(lambda request: httpx.Response(401, text="sensitive-upstream-body"))
        with self.assertRaisesRegex(ValueError, "rejected the API key") as error:
            await self.client.generate_recipe("Dinner", {})
        self.assertNotIn("sensitive-upstream-body", str(error.exception))

    async def test_grocery_validation_retry(self):
        calls = []
        def handle(request):
            payload = json.loads(request.content)
            calls.append(payload)
            data = {"items": [{"ingredient_name": "rice"}]} if len(calls) == 1 else {"items": []}
            return httpx.Response(200, json=completion("generate_grocery_list", data))
        self.transport(handle)
        result = await self.client.generate_grocery_list([], [], [])
        self.assertEqual(result.items, [])
        self.assertEqual(len(calls), 2)
        self.assertIsInstance(calls[1]["messages"][1]["content"], str)

    def test_truncated_response_rejected(self):
        with self.assertRaisesRegex(ValueError, "truncated"):
            _extract_tool_input(completion("generate_recipe", RECIPE, "length"), "generate_recipe")

    async def test_truncated_recipe_retries_with_larger_budget(self):
        calls = []
        def handle(request):
            payload = json.loads(request.content)
            calls.append(payload)
            if len(calls) == 1:
                result = completion("generate_recipe", RECIPE, "length")
                result["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = '{"title":'
                return httpx.Response(200, json=result)
            return httpx.Response(200, json=completion("generate_recipe", RECIPE))
        self.transport(handle)
        result = await self.client.generate_recipe("Dinner", {})
        self.assertEqual(result.title, RECIPE["title"])
        self.assertEqual([c["max_tokens"] for c in calls], [8192, 16384])
        self.assertEqual(calls[0]["messages"], calls[1]["messages"])

    async def test_persistent_truncation_stops_after_one_retry(self):
        calls = []
        def handle(request):
            calls.append(json.loads(request.content))
            return httpx.Response(200, json=completion("generate_recipe", RECIPE, "length"))
        self.transport(handle)
        with self.assertRaisesRegex(ValueError, "truncated"):
            await self.client.generate_recipe("Dinner", {})
        self.assertEqual(len(calls), 2)

    async def test_truncated_stream_recovers_with_complete_recipe(self):
        calls = []
        def handle(request):
            payload = json.loads(request.content)
            calls.append(payload)
            if payload["stream"]:
                frame = {"choices": [{"delta": {"tool_calls": [{"index": 0,
                    "function": {"name": "generate_recipe", "arguments": '{"title":'}}]},
                    "finish_reason": "length"}]}
                return httpx.Response(200, text="data: " + json.dumps(frame) + "\n\ndata: [DONE]\n\n")
            return httpx.Response(200, json=completion("generate_recipe", RECIPE))
        self.transport(handle)
        events = [json.loads(e[6:].strip()) async for e in self.client.generate_recipe_stream("Dinner", {})]
        self.assertEqual(events[-1]["recipe"]["title"], RECIPE["title"])
        self.assertEqual([c["max_tokens"] for c in calls], [8192, 16384])

    def test_missing_tool_rejected(self):
        with self.assertRaisesRegex(ValueError, "expected"):
            _extract_tool_input(completion("wrong_tool", {}), "generate_recipe")


class SettingsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        async def override_db():
            async with self.sessions() as session:
                yield session
                await session.commit()
        app = FastAPI()
        app.include_router(router, prefix="/api")
        app.include_router(recipes_router, prefix="/api")
        self.app = app
        app.dependency_overrides[get_db] = override_db
        self.http = TestClient(app)
        self.env = patch.object(settings, "openrouter_api_key", "")
        self.env.start()

    async def asyncTearDown(self):
        self.env.stop()
        self.http.close()
        await self.engine.dispose()

    async def test_key_is_write_only_and_survives_preference_updates(self):
        response = self.http.put("/api/settings", json={"openRouterApiKey": " test-key "})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["hasOpenRouterKey"])
        self.assertNotIn("test-key", response.text)
        self.http.put("/api/settings", json={"maxDifficulty": "easy"})
        self.http.put("/api/settings", json={"openRouterApiKey": ""})
        response = self.http.get("/api/settings")
        self.assertTrue(response.json()["hasOpenRouterKey"])
        self.assertNotIn("openRouterApiKey", response.json())
        async with self.sessions() as session:
            dependency = get_llm_client(session)
            client = await anext(dependency)
            self.assertEqual(client._client.headers["Authorization"], "Bearer test-key")
            await dependency.aclose()

    async def test_updated_credentials_apply_to_next_request(self):
        self.http.put("/api/settings", json={"openRouterApiKey": "first", "openRouterModel": "provider/first"})
        self.http.put("/api/settings", json={"openRouterApiKey": "second", "openRouterModel": "provider/second"})
        async with self.sessions() as session:
            dependency = get_llm_client(session)
            client = await anext(dependency)
            self.assertEqual(client.model, "provider/second")
            self.assertEqual(client._client.headers["Authorization"], "Bearer second")
            await dependency.aclose()

    async def test_remove_key_and_environment_fallback(self):
        self.http.put("/api/settings", json={"openRouterApiKey": "saved"})
        with patch.object(settings, "openrouter_api_key", "environment-key"):
            response = self.http.put("/api/settings", json={"openRouterApiKey": None})
            self.assertEqual(response.json()["openRouterKeySource"], "environment")
        self.assertFalse(self.http.get("/api/settings").json()["hasOpenRouterKey"])

    async def test_missing_key_is_actionable(self):
        self.assertEqual(self.http.get("/api/settings").status_code, 200)
        async with self.sessions() as session:
            dependency = get_llm_client(session)
            with self.assertRaises(Exception) as error:
                await anext(dependency)
            self.assertEqual(error.exception.status_code, 503)
            self.assertIn("Settings", error.exception.detail)

    async def test_invalid_configuration_rejected(self):
        for body in [{"openRouterModel": ""}, {"openRouterModel": "no-provider"}, {"openRouterApiKey": 123}]:
            self.assertEqual(self.http.put("/api/settings", json=body).status_code, 422)

    async def test_recipe_stream_returns_error_event_and_done(self):
        class FailingClient:
            async def generate_recipe_stream(self, concept, constraints):
                raise ValueError("OpenRouter rejected the API key. Update it in Settings.")
                yield  # Keep this an async generator.
        async def override_client():
            yield FailingClient()
        self.app.dependency_overrides[get_llm_client] = override_client
        response = self.http.post("/api/recipes/generate", json={"concept": "Dinner"},
                                  headers={"Accept": "text/event-stream"})
        self.assertEqual(response.status_code, 200)
        self.assertIn('"error":', response.text)
        self.assertIn("rejected the API key", response.text)
        self.assertTrue(response.text.endswith("data: [DONE]\n\n"))
