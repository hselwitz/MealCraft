import {useEffect, useState} from "react";
import {Bookmark, Check} from "lucide-react";
import type {RepertoireMeal} from "@/api/discovery";
import {useMealFeedback} from "@/hooks/useRepertoire";
import {Button} from "./ui/button";

export function CookingFeedback({meal, recipeId}: {meal?: RepertoireMeal; recipeId?: string}) {
    const feedback = useMealFeedback(recipeId);
    const [notes, setNotes] = useState(meal?.notes ?? "");
    const [noteSaved, setNoteSaved] = useState(false);
    const [cooked, setCooked] = useState(false);
    useEffect(() => {setNotes(meal?.notes ?? "");}, [meal?.notes]);
    const send = (body: Parameters<typeof feedback.mutate>[0]["body"]) => feedback.mutate({id: meal?.id ?? "", body});
    return <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
            <Button variant={meal?.saved ? "secondary" : "primary"} disabled={feedback.isPending} onClick={() => send({saved: !meal?.saved})}><Bookmark size={15}/>{meal?.saved ? "Saved · remove" : "Save to repertoire"}</Button>
            <Button variant="outline" disabled={feedback.isPending || cooked} onClick={() => feedback.mutate({id: meal?.id ?? "", body: {cooked: true}}, {onSuccess: () => setCooked(true)})}><Check size={15}/>{cooked ? "Cooking logged" : "I cooked this"}</Button>
        </div>
        <fieldset disabled={feedback.isPending}><legend className="text-sm font-semibold mb-2">Would you make it again?</legend>
            <div className="flex flex-wrap gap-2">{([["again", "Make again"], ["adjust", "Needs changes"], ["no", "Not for me"]] as const).map(([value, label]) => <button key={value} aria-pressed={meal?.verdict === value} onClick={() => send({verdict: value})} className={`text-xs rounded-lg border px-3 py-2 ${meal?.verdict === value ? "bg-primary-50 border-primary-400 text-primary-800" : "border-gray-200 text-gray-600"}`}>{label}</button>)}</div>
        </fieldset>
        <fieldset disabled={feedback.isPending}><legend className="text-sm font-semibold mb-2">Was it easy enough?</legend>
            <div className="flex gap-2">{([[true, "Yes, easy enough"], [false, "Too much effort"]] as const).map(([value, label]) => <button key={label} aria-pressed={meal?.easy_enough === value} onClick={() => send({easy_enough: value})} className={`text-xs rounded-lg border px-3 py-2 ${meal?.easy_enough === value ? "bg-primary-50 border-primary-400 text-primary-800" : "border-gray-200 text-gray-600"}`}>{label}</button>)}</div>
        </fieldset>
        <div><label className="block text-sm font-semibold mb-2" htmlFor={`notes-${recipeId ?? meal?.id}`}>Your cooking notes</label>
            <textarea id={`notes-${recipeId ?? meal?.id}`} value={notes} maxLength={2000} rows={2} onChange={(e) => {setNotes(e.target.value); setNoteSaved(false);}} placeholder="What worked? What would you change?" className="border border-gray-300 rounded-lg p-3 w-full text-sm"/>
            <Button size="sm" variant="ghost" disabled={feedback.isPending} onClick={() => feedback.mutate({id: meal?.id ?? "", body: {notes}}, {onSuccess: () => setNoteSaved(true)})}>{noteSaved ? "Notes saved" : "Save notes"}</Button>
        </div>
        {meal?.cooked_count ? <p className="text-xs text-gray-500">Cooked {meal.cooked_count} {meal.cooked_count === 1 ? "time" : "times"}{meal.last_cooked_at ? ` · Last cooked ${new Date(meal.last_cooked_at).toLocaleDateString()}` : ""}</p> : null}
        {feedback.error && <p role="alert" className="text-sm text-red-600">{feedback.error.message}</p>}
    </div>;
}
