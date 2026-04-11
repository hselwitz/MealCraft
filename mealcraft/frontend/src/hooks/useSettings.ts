import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import {settingsApi} from "@/api/settings";

export interface AppSettings {
    maxDifficulty: "easy" | "medium" | "hard";
    ingredientOverlap: "low" | "medium" | "high";
    defaultServings: number;
    calorieTarget: number;
    cuisinePreferences: string[];
    dietaryRestrictions: string[];
    pantryStaples: string[];
    mealPrepFocus: boolean;
}

export const DEFAULT_SETTINGS: AppSettings = {
    maxDifficulty: "medium",
    ingredientOverlap: "medium",
    defaultServings: 2,
    calorieTarget: 2500,
    cuisinePreferences: [],
    dietaryRestrictions: [],
    pantryStaples: [
        "salt", "black pepper", "olive oil", "vegetable oil",
        "sugar", "all-purpose flour", "baking soda", "baking powder",
    ],
    mealPrepFocus: false,
};

export function useSettings() {
    const qc = useQueryClient();

    const {data} = useQuery({
        queryKey: ["settings"],
        queryFn: settingsApi.get,
        staleTime: Infinity,
    });

    const mutation = useMutation({
        mutationFn: settingsApi.update,
        onSuccess: (updated) => qc.setQueryData(["settings"], updated),
    });

    const settings: AppSettings = data ? {...DEFAULT_SETTINGS, ...data} : DEFAULT_SETTINGS;

    // Same [settings, setSettings] API as before — setSettings accepts value or updater fn
    const setSettings = (updater: AppSettings | ((prev: AppSettings) => AppSettings)) => {
        const next = typeof updater === "function" ? updater(settings) : updater;
        mutation.mutate(next);
    };

    return [settings, setSettings] as const;
}
