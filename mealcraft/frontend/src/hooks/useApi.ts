import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import {plansApi} from "@/api/plans";
import {recipesApi} from "@/api/recipes";
import {leftoversApi} from "@/api/leftovers";
import {groceryApi} from "@/api/grocery";
import type {CreateLeftoverRequest, CreatePlanRequest, GenerateRecipeRequest, UpdateSlotRequest,} from "@/types";

// ─── Plans ───────────────────────────────────────────────────────────────────

export function usePlans() {
    return useQuery({
        queryKey: ["plans"],
        queryFn: () => plansApi.list(),
    });
}

export function usePlan(id: string | undefined) {
    return useQuery({
        queryKey: ["plans", id],
        queryFn: () => plansApi.get(id!),
        enabled: !!id,
    });
}

export function useCreatePlan() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (body: CreatePlanRequest) => plansApi.create(body),
        onSuccess: () => qc.invalidateQueries({queryKey: ["plans"]}),
    });
}

export function useUpdateSlot() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({
                         planId,
                         slotId,
                         body,
                     }: {
            planId: string;
            slotId: string;
            body: UpdateSlotRequest;
        }) => plansApi.updateSlot(planId, slotId, body),
        onSuccess: (_data, vars) => {
            qc.invalidateQueries({queryKey: ["plans", vars.planId]});
        },
    });
}

export function useRegenerateSlot() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({planId, slotId}: { planId: string; slotId: string }) =>
            plansApi.regenerateSlot(planId, slotId),
        onSuccess: (_data, vars) => {
            qc.invalidateQueries({queryKey: ["plans", vars.planId]});
        },
    });
}

export function useGeneratePlan() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({planId, preferences}: { planId: string; preferences?: object }) =>
            plansApi.generate(planId, preferences),
        onSuccess: (_data, vars) => {
            qc.invalidateQueries({queryKey: ["plans", vars.planId]});
            qc.invalidateQueries({queryKey: ["plans"]});
        },
    });
}

export function useCurrentPrepPlan(planId: string | undefined) {
    return useQuery({
        queryKey: ["prep-plan", planId],
        queryFn: () => plansApi.getCurrentPrepPlan(planId!),
        enabled: !!planId,
        retry: false, // 404 means no plan yet — don't retry
    });
}

export function usePatchPrepPlan() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({planId, completedTasks}: { planId: string; completedTasks: string[] }) =>
            plansApi.patchPrepPlan(planId, {completed_tasks: completedTasks}),
        onSuccess: (_data, vars) => qc.invalidateQueries({queryKey: ["prep-plan", vars.planId]}),
    });
}

export function useGeneratePrepPlan() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({planId, timeWindows}: { planId: string; timeWindows?: string[] }) =>
            plansApi.generatePrepPlan(planId, timeWindows),
        onSuccess: (_data, vars) => qc.invalidateQueries({queryKey: ["prep-plan", vars.planId]}),
    });
}

export function useCurrentGroceryList(planId: string | undefined) {
    return useQuery({
        queryKey: ["grocery", "current", planId],
        queryFn: () => plansApi.getCurrentGroceryList(planId!),
        enabled: !!planId,
        retry: false,
    });
}

export function useGenerateGroceryList() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({planId, pantryStaples}: { planId: string; pantryStaples?: string[] }) =>
            plansApi.generateGroceryList(planId, pantryStaples),
        onSuccess: (_data, vars) => qc.invalidateQueries({queryKey: ["grocery", "current", vars.planId]}),
    });
}

// ─── Recipes ─────────────────────────────────────────────────────────────────

export function useRecipe(id: string | undefined) {
    return useQuery({
        queryKey: ["recipes", id],
        queryFn: () => recipesApi.get(id!),
        enabled: !!id,
    });
}

export function useRecipes() {
    return useQuery({
        queryKey: ["recipes"],
        queryFn: () => recipesApi.list(),
    });
}

export function useGenerateRecipe() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (body: GenerateRecipeRequest) => recipesApi.generate(body),
        onSuccess: () => qc.invalidateQueries({queryKey: ["recipes"]}),
    });
}

// ─── Leftovers ───────────────────────────────────────────────────────────────

export function useLeftovers(status?: string) {
    return useQuery({
        queryKey: ["leftovers", status ?? "available"],
        queryFn: () => leftoversApi.list(status ?? "available"),
    });
}

export function useCreateLeftover() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (body: CreateLeftoverRequest) => leftoversApi.create(body),
        onSuccess: () => qc.invalidateQueries({queryKey: ["leftovers"]}),
    });
}

export function useUpdateLeftover() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({
                         id,
                         body,
                     }: {
            id: string;
            body: { status?: string; remaining_servings?: number; used_in_slot_id?: string };
        }) => leftoversApi.update(id, body),
        onSuccess: () => qc.invalidateQueries({queryKey: ["leftovers"]}),
    });
}

export function useLeftoverSuggestions() {
    return useMutation({
        mutationFn: (emptySlots?: string[]) => leftoversApi.getSuggestions(emptySlots),
    });
}

// ─── Grocery ─────────────────────────────────────────────────────────────────

export function useGroceryList(id: string | undefined) {
    return useQuery({
        queryKey: ["grocery", id],
        queryFn: () => groceryApi.get(id!),
        enabled: !!id,
    });
}

export function useToggleGroceryItem() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({
                         listId,
                         itemId,
                         checked,
                     }: {
            listId: string;
            itemId: string;
            checked: boolean;
        }) => groceryApi.updateItem(listId, itemId, {checked}),
        onSuccess: (_data, vars) => {
            qc.invalidateQueries({queryKey: ["grocery", vars.listId]});
        },
    });
}
