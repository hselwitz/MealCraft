import {apiDelete, apiGet, apiPatch, apiPost, apiPut} from "./client";
import type {
    CreatePlanRequest,
    GroceryList,
    MealPlan,
    MealPlanListItem,
    MealSlot,
    PrepPlan,
    UpdateSlotRequest,
} from "@/types";

export const plansApi = {
    list: (cursor?: string) =>
        apiGet<MealPlanListItem[]>("/plans", cursor ? {cursor} : undefined),

    get: (id: string) => apiGet<MealPlan>(`/plans/${id}`),

    create: (body: CreatePlanRequest) => apiPost<MealPlan>("/plans", body),

    update: (id: string, body: { name?: string; status?: string; calorie_target?: number }) =>
        apiPatch<MealPlan>(`/plans/${id}`, body),

    updateSlot: (planId: string, slotId: string, body: UpdateSlotRequest) =>
        apiPut<MealSlot>(`/plans/${planId}/slots/${slotId}`, body),

    regenerateSlot: (planId: string, slotId: string) =>
        apiPost<MealSlot>(`/plans/${planId}/slots/${slotId}/regenerate`),

    generate: (planId: string, preferences?: object) =>
        apiPost<MealPlan>(`/plans/${planId}/generate`, {preferences: preferences ?? {}}),

    generatePrepPlan: (planId: string, timeWindows?: string[]) =>
        apiPost<PrepPlan>(`/plans/${planId}/prep-plan`, {
            time_windows: timeWindows ?? ["Sunday afternoon", "Wednesday evening"],
        }),

    generateGroceryList: (planId: string, pantryStaples?: string[]) =>
        apiPost<{
            grocery_list_id: string;
            status: string
        }>(`/plans/${planId}/grocery-list`, pantryStaples ? {pantry_staples: pantryStaples} : undefined),

    getCurrentPrepPlan: (planId: string) =>
        apiGet<PrepPlan>(`/plans/${planId}/prep-plan/current`),

    patchPrepPlan: (planId: string, body: { completed_tasks: string[] }) =>
        apiPatch<PrepPlan>(`/plans/${planId}/prep-plan/current`, body),

    createSlot: (planId: string, date: string, mealType: string) =>
        apiPost(`/plans/${planId}/slots`, {date, meal_type: mealType}),

    deleteSlot: (planId: string, slotId: string) =>
        apiDelete(`/plans/${planId}/slots/${slotId}`),

    getCurrentGroceryList: (planId: string) =>
        apiGet<GroceryList>(`/plans/${planId}/grocery-list/current`),
};
