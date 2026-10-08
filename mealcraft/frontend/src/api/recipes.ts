import {apiDelete, apiGet, apiPost} from "./client";
import type {GenerateRecipeRequest, Recipe} from "@/types";

export const recipesApi = {
    list: (cursor?: string) =>
        apiGet<Recipe[]>("/recipes", cursor ? {cursor, limit: "100"} : {limit: "100"}),

    get: (id: string) => apiGet<Recipe>(`/recipes/${id}`),

    generate: (body: GenerateRecipeRequest) => apiPost<Recipe>("/recipes/generate", body),

    delete: (id: string) => apiDelete(`/recipes/${id}`),
};
