import {useState} from "react";
import {BookOpen, Trash2, Wand2} from "lucide-react";
import {useDeleteRecipe, useGenerateRecipe, usePlan, usePlans, useRecipes} from "@/hooks/useApi";
import type {RecipeSummary} from "@/types";
import {Button} from "@/components/ui/button";
import {Input} from "@/components/ui/input";
import {RecipeCard} from "@/components/RecipeCard";
import {RecipeCardSkeleton} from "@/components/ui/skeleton";

export function RecipesList() {
    const {data: recipes, isLoading} = useRecipes();
    const {data: plans} = usePlans();
    const generateRecipe = useGenerateRecipe();
    const deleteRecipe = useDeleteRecipe();
    const [showAll, setShowAll] = useState(false);
    const [showGenerateForm, setShowGenerateForm] = useState(false);
    const [concept, setConcept] = useState("");
    const [restrictions, setRestrictions] = useState("");

    const activePlan = plans?.find((p) => p.status === "active" || p.status === "draft");
    const {data: plan} = usePlan(activePlan?.id);

    const planRecipeIds = new Set(
        plan?.slots.map((s) => s.recipe_id).filter(Boolean) ?? []
    );

    const visibleRecipes = showAll ? recipes : recipes?.filter((r) => planRecipeIds.has(r.id));

    const handleGenerate = async () => {
        if (!concept.trim()) return;
        await generateRecipe.mutateAsync({
            concept: concept.trim(),
            dietary_restrictions: restrictions
                ? restrictions.split(",").map((s) => s.trim()).filter(Boolean)
                : [],
            max_difficulty: "medium",
            target_servings: 4,
        });
        setConcept("");
        setRestrictions("");
        setShowGenerateForm(false);
    };

    const handleDelete = async (id: string, e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        await deleteRecipe.mutateAsync(id);
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Recipes</h1>
                    <p className="text-sm text-gray-500 mt-1">
                        {visibleRecipes?.length ?? 0} recipe{visibleRecipes?.length !== 1 ? "s" : ""}
                        {!showAll && ` in current plan`}
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setShowAll((v) => !v)}
                        className={[
                            "text-sm px-3 py-1.5 rounded-lg border transition-colors",
                            showAll
                                ? "bg-gray-100 border-gray-300 text-gray-700"
                                : "bg-white border-gray-200 text-gray-500 hover:bg-gray-50",
                        ].join(" ")}
                    >
                        {showAll ? "Current plan" : "All recipes"}
                    </button>
                    <Button onClick={() => setShowGenerateForm(!showGenerateForm)} className="flex items-center gap-2">
                        <Wand2 size={16}/>
                        Generate Recipe
                    </Button>
                </div>
            </div>

            {showGenerateForm && (
                <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3 shadow-sm">
                    <h3 className="font-semibold text-gray-800">Generate New Recipe</h3>
                    <Input
                        label="Meal concept"
                        placeholder="e.g. Spicy Thai peanut noodles with tofu"
                        value={concept}
                        onChange={(e) => setConcept(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
                    />
                    <Input
                        label="Dietary restrictions (optional)"
                        placeholder="e.g. vegetarian, gluten-free"
                        value={restrictions}
                        onChange={(e) => setRestrictions(e.target.value)}
                        hint="Comma-separated list"
                    />
                    <div className="flex gap-2">
                        <Button onClick={handleGenerate} loading={generateRecipe.isPending} disabled={!concept.trim()}>
                            Generate
                        </Button>
                        <Button variant="ghost" onClick={() => setShowGenerateForm(false)}>
                            Cancel
                        </Button>
                    </div>
                </div>
            )}

            {!isLoading && visibleRecipes?.length === 0 && (
                <div className="text-center py-16 text-gray-400">
                    <BookOpen size={48} className="mx-auto mb-3 opacity-30"/>
                    {showAll
                        ? <p>No recipes yet.</p>
                        : <><p>No recipes in your current plan.</p>
                            <button onClick={() => setShowAll(true)} className="text-sm text-primary-500 mt-1 hover:underline">
                                Browse all recipes
                            </button></>
                    }
                </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {isLoading
                    ? Array.from({length: 6}).map((_, i) => <RecipeCardSkeleton key={i}/>)
                    : visibleRecipes?.map((recipe) => (
                        <div key={recipe.id} className="relative group">
                            <RecipeCard recipe={recipe as unknown as RecipeSummary}/>
                            {showAll && !planRecipeIds.has(recipe.id) && (
                                <button
                                    onClick={(e) => handleDelete(recipe.id, e)}
                                    className="absolute top-2 right-2 p-1.5 rounded-lg bg-white/90 text-gray-400 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-all shadow-sm"
                                    title="Delete recipe"
                                >
                                    <Trash2 size={14}/>
                                </button>
                            )}
                        </div>
                    ))
                }
            </div>
        </div>
    );
}
