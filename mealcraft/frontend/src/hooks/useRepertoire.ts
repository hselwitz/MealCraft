import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import {discoveryApi, type MealFeedback} from "@/api/discovery";

export function useRepertoire() {
    return useQuery({queryKey: ["repertoire"], queryFn: discoveryApi.repertoire});
}
export function useMealFeedback(recipeId?: string) {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: ({id, body}: {id: string; body: MealFeedback}) => recipeId
            ? discoveryApi.updateRecipe(recipeId, body) : discoveryApi.updateMeal(id, body),
        onSuccess: () => qc.invalidateQueries({queryKey: ["repertoire"]}),
    });
}
