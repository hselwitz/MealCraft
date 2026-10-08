import {KitchenArt} from "@/components/KitchenArt";
import {useState} from "react";
import {Link, useNavigate, useSearchParams} from "react-router-dom";
import {ArrowRight, Clock, Sparkles, Utensils} from "lucide-react";
import {useMutation, useQueryClient} from "@tanstack/react-query";
import {discoveryApi, type DinnerIdea, type Direction, type DiscoveryRequest} from "@/api/discovery";
import {useRepertoire} from "@/hooks/useRepertoire";
import {useSettings} from "@/hooks/useSettings";
import {useLocalStorage} from "@/hooks/useLocalStorage";
import {usePlanningWindow} from "@/hooks/usePlanningWindow";
import {Button} from "@/components/ui/button";

const directions: {value: Direction; title: string; description: string}[] = [
    {value: "usual", title: "Keep my usual method", description: "A new seasoning, topping, or side."},
    {value: "twist", title: "One easy change", description: "A little variety, familiar effort."},
    {value: "new", title: "Try a new dish", description: "Something different, still convenient."},
];

export function Discover() {
    const {window, valid} = usePlanningWindow();
    const navigate = useNavigate();
    const qc = useQueryClient();
    const [params] = useSearchParams();
    const [settings] = useSettings();
    const {data: repertoire, isLoading, error: repertoireError} = useRepertoire();
    const [request, setRequest] = useState("");
    const [direction, setDirection] = useState<Direction>("twist");
    const [budget, setBudget] = useState(15);
    const [mealId, setMealId] = useState(params.get("meal") ?? "");
    const [results, setResults] = useLocalStorage<{ideas: DinnerIdea[]; request: DiscoveryRequest} | null>("mealcraft-discovery-v1", null);
    const ideas = useMutation({mutationFn: discoveryApi.ideas, onSuccess: (data, body) => setResults({ideas: data.ideas, request: body})});
    const recipe = useMutation({mutationFn: discoveryApi.recipe, onSuccess: (data) => {
        qc.invalidateQueries({queryKey: ["recipes"]});
        navigate(`/recipes/${data.id}`);
    }});
    const busy = ideas.isPending || recipe.isPending;
    const familiar = repertoire?.filter((meal) => meal.familiar || meal.saved) ?? [];
    const error = ideas.error || recipe.error;
    const findIdeas = () => {
        recipe.reset();
        ideas.mutate({request, direction, planning_start_date: window.start_date, planning_end_date: window.end_date, max_active_min: budget, familiar_meal_id: mealId || undefined,
            avoid_titles: results?.ideas.map((idea) => idea.title)});
    };
    const cook = (idea: DinnerIdea) => {
        if (!results) return;
        ideas.reset();
        recipe.mutate({idea, max_active_min: results.request.max_active_min, request: results.request.request});
    };

    return <div className="max-w-5xl mx-auto space-y-8">
        <header className="kitchen-hero"><div>
            <p className="text-xs font-semibold tracking-widest uppercase text-primary-700 mb-3">A little variety. The same easy evening.</p>
            <h1 className="text-3xl sm:text-4xl kitchen-title text-gray-900">What should we prep next?</h1>
            <p className="mt-3 text-gray-500 max-w-xl">Find convenient variations that fit your meal prep plan. Choose recipes, schedule portions, then shop and prep them together.</p></div><KitchenArt variant="discover" className="hidden sm:block w-40 shrink-0"/>
        </header>

        {!settings.hasOpenRouterKey && <div className="rounded-xl border border-primary-200 bg-primary-50 p-4 text-sm text-primary-900">
            Add your OpenRouter key in <Link to="/settings" className="font-semibold underline">Settings</Link> to get dinner ideas. Your usual meals are ready in <Link to="/repertoire" className="underline">Repertoire</Link>.
        </div>}

        <form onSubmit={(e) => {e.preventDefault(); findIdeas();}} className="rounded-2xl bg-white border border-gray-200 p-5 sm:p-7 shadow-sm space-y-6">
            <div>
                <label htmlFor="dinner-request" className="block font-semibold text-gray-900 mb-2">What are you working with?</label>
                <textarea id="dinner-request" value={request} maxLength={2000} disabled={busy}
                    onChange={(e) => setRequest(e.target.value)} rows={2}
                    placeholder="Chicken breast, frozen peppers, rice… or just a craving."
                    className="w-full rounded-xl border border-gray-300 px-4 py-3 text-sm focus:ring-2 focus:ring-primary-300 focus:outline-none"/>
                <p className="text-xs text-gray-500 mt-2">Optional. Frozen vegetables, jarred sauces, and microwave shortcuts are welcome.</p>
            </div>
            <fieldset disabled={busy}>
                <legend className="font-semibold text-gray-900 mb-3">How much should change?</legend>
                <div className="grid sm:grid-cols-3 gap-3">
                    {directions.map((option) => <label key={option.value} className={`cursor-pointer rounded-xl border p-4 ${direction === option.value ? "bg-primary-50 border-primary-400" : "border-gray-200 hover:bg-gray-50"}`}>
                        <div className="flex items-center gap-2"><input type="radio" name="direction" value={option.value} checked={direction === option.value} onChange={() => setDirection(option.value)} className="accent-green-600"/><span className="text-sm font-semibold">{option.title}</span></div>
                        <p className="text-xs text-gray-500 mt-2">{option.description}</p>
                    </label>)}
                </div>
            </fieldset>
            <div className="grid sm:grid-cols-2 gap-5">
                <div><label htmlFor="familiar-meal" className="block text-sm font-semibold mb-2">Start from a familiar meal</label>
                    <select id="familiar-meal" value={mealId} disabled={busy || isLoading} onChange={(e) => setMealId(e.target.value)} className="w-full border border-gray-300 rounded-lg p-2.5 text-sm">
                        <option value="">Any of my meals</option>
                        {familiar.map((meal) => <option key={meal.id} value={meal.id}>{meal.title}</option>)}
                    </select>
                    {repertoireError && <p role="alert" className="text-xs text-red-600 mt-2">Could not load your repertoire. Try refreshing.</p>}
                </div>
                <div><label htmlFor="hands-on" className="block text-sm font-semibold mb-2">How much hands-on time?</label>
                    <select id="hands-on" value={budget} disabled={busy} onChange={(e) => setBudget(Number(e.target.value))} className="w-full border border-gray-300 rounded-lg p-2.5 text-sm">
                        {[10, 15, 25, 40].map((minutes) => <option key={minutes} value={minutes}>Up to {minutes} minutes</option>)}
                    </select>
                    <p className="text-xs text-gray-500 mt-2">Oven and simmering time are shown separately.</p>
                </div>
            </div>
            <Button type="submit" size="lg" loading={ideas.isPending} disabled={recipe.isPending || !settings.hasOpenRouterKey || !valid} className="w-full sm:w-auto">
                <Sparkles size={18}/>{ideas.isPending ? "Finding easy ideas…" : results ? "Find three different ideas" : "Find three meal ideas"}
            </Button>
        </form>

        {error && <div role="alert" className="rounded-xl bg-red-50 border border-red-200 p-4 text-sm text-red-700">{error.message}</div>}
        {results && <section aria-label="Dinner ideas" className="space-y-4">
            <div><h2 className="text-xl font-bold">Three ways to change things up</h2><p className="text-sm text-gray-500 mt-1">Up to {results.request.max_active_min} minutes hands-on. Times are estimates; choose a recipe, then add it to your prep plan.</p></div>
            <div className="grid md:grid-cols-3 gap-4">
                {results.ideas.map((idea, index) => <article key={`${idea.title}-${index}`} className="workflow-card rounded-2xl p-5 flex flex-col gap-4">
                    <span className="text-xs font-semibold text-primary-700">DINNER {index + 1}</span>
                    <div><h3 className="text-lg font-bold leading-snug">{idea.title}</h3><p className="text-sm text-gray-500 mt-2">{idea.description}</p></div>
                    <div className="text-sm space-y-2">
                        <p className="flex items-center gap-2 font-medium"><Clock size={15}/>{idea.active_time_min} min hands-on · {idea.total_time_min} min total</p>
                        <p className="flex items-start gap-2 text-gray-600"><Utensils size={15} className="shrink-0 mt-0.5"/>{idea.cleanup}</p>
                    </div>
                    <p className="text-sm text-gray-600">{idea.familiar_connection}</p>
                    <div className="rounded-lg bg-gray-50 p-3 text-xs text-gray-600"><span className="font-semibold">Easy shortcut: </span>{idea.convenience_tip}</div>
                    <p className="text-xs text-gray-500"><span className="font-semibold">Extra ingredients: </span>{idea.extra_ingredients.length ? idea.extra_ingredients.join(", ") : "No extras suggested"}</p>
                    <Button onClick={() => cook(idea)} disabled={busy || !settings.hasOpenRouterKey} loading={recipe.isPending && recipe.variables?.idea.title === idea.title} className="mt-auto">
                        {recipe.isPending && recipe.variables?.idea.title === idea.title ? "Writing your recipe…" : "Get this recipe"}<ArrowRight size={15}/>
                    </Button>
                </article>)}
            </div>
        </section>}
        <Link to="/repertoire" className="inline-flex items-center gap-2 text-sm font-medium text-primary-700">Browse your repertoire <ArrowRight size={15}/></Link>
    </div>;
}
