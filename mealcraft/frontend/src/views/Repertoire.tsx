import {useState} from "react";
import {Link} from "react-router-dom";
import {useMutation, useQueryClient} from "@tanstack/react-query";
import {BookOpen, Plus, ArrowRight} from "lucide-react";
import {discoveryApi} from "@/api/discovery";
import {useRepertoire} from "@/hooks/useRepertoire";
import {CookingFeedback} from "@/components/CookingFeedback";
import {Button} from "@/components/ui/button";

export function Repertoire() {
    const {data: meals, isLoading, error} = useRepertoire();
    const qc = useQueryClient();
    const [filter, setFilter] = useState<"saved" | "familiar" | "cooked">("saved");
    const [showAdd, setShowAdd] = useState(false);
    const [title, setTitle] = useState("");
    const [notes, setNotes] = useState("");
    const add = useMutation({mutationFn: discoveryApi.addMeal, onSuccess: () => {
        qc.invalidateQueries({queryKey: ["repertoire"]}); setTitle(""); setNotes(""); setShowAdd(false); setFilter("saved");
    }});
    const visible = (meals ?? []).filter((meal) => filter === "familiar" ? meal.familiar : filter === "cooked" ? meal.cooked_count > 0 : meal.saved);
    if (filter === "cooked") visible.sort((a, b) => (b.last_cooked_at ?? "").localeCompare(a.last_cooked_at ?? ""));
    return <div className="max-w-5xl mx-auto space-y-6">
        <header className="flex flex-wrap gap-4 items-start justify-between"><div><h1 className="text-3xl font-bold">Your repertoire</h1><p className="text-gray-500 mt-2">Your usual meals, new favorites, and the notes that make them yours.</p></div><Button onClick={() => setShowAdd(!showAdd)}><Plus size={16}/>Add a meal</Button></header>
        {showAdd && <form onSubmit={(e) => {e.preventDefault(); add.mutate({title: title.trim(), notes});}} className="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
            <h2 className="font-semibold">Something you already cook</h2>
            <label className="block text-sm">Meal name<input required maxLength={255} value={title} onChange={(e) => setTitle(e.target.value)} className="block w-full border rounded-lg p-2 mt-1" placeholder="e.g. My weeknight chicken bowl"/></label>
            <label className="block text-sm">Ingredients or your usual method<textarea maxLength={2000} value={notes} onChange={(e) => setNotes(e.target.value)} className="block w-full border rounded-lg p-2 mt-1" placeholder="A quick description is enough. No detailed recipe needed."/></label>
            <Button type="submit" loading={add.isPending} disabled={!title.trim()}>Add to repertoire</Button>
            {add.error && <p role="alert" className="text-sm text-red-600">{add.error.message}</p>}
        </form>}
        <div className="flex flex-wrap gap-2">{([["saved", "Saved meals"], ["familiar", "My usual meals"], ["cooked", "Recently cooked"]] as const).map(([value, label]) => <Button key={value} variant={filter === value ? "primary" : "secondary"} onClick={() => setFilter(value)} aria-pressed={filter === value}>{label}</Button>)}</div>
        {error && <p role="alert" className="text-red-600 text-sm">{error.message}</p>}
        {isLoading && <p className="text-gray-500" role="status">Loading your repertoire…</p>}
        {!isLoading && !error && !visible.length && <div className="rounded-xl border border-dashed p-8 text-center text-gray-500"><BookOpen className="mx-auto mb-3"/><p>{filter === "cooked" ? "Mark a meal as cooked to start your history." : "Save a recipe or add one of your usual meals."}</p><Link to="/discover" className="inline-block text-primary-700 mt-3">Find a dinner idea</Link></div>}
        <div className="grid md:grid-cols-2 gap-4">{visible.map((meal) => <article key={meal.id} className="bg-white rounded-xl border border-gray-200 p-5 space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-primary-700">{meal.familiar ? "Your usual" : "Saved recipe"}</p>
            <h2 className="text-lg font-semibold">{meal.title}</h2><p className="text-sm text-gray-500 whitespace-pre-wrap">{meal.notes}</p>
            <div className="flex flex-wrap gap-4 text-sm font-medium text-primary-700">{meal.recipe_id && <Link to={`/recipes/${meal.recipe_id}`}>Open recipe</Link>}<Link to={`/discover?meal=${encodeURIComponent(meal.id)}`} className="inline-flex items-center gap-1">Find an easy variation<ArrowRight size={14}/></Link></div>
            <details className="border-t pt-3"><summary className="text-sm text-gray-600 cursor-pointer">Cooking feedback & notes{meal.verdict === "again" ? " · Make again" : meal.verdict === "adjust" ? " · Needs changes" : meal.verdict === "no" ? " · Not for me" : ""}</summary><div className="pt-4"><CookingFeedback meal={meal} recipeId={meal.recipe_id ?? undefined}/></div></details>
        </article>)}</div>
        <Link to="/recipes" className="text-sm text-gray-500 hover:text-primary-700 inline-block">Browse all generated recipes</Link>
    </div>;
}
