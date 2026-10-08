import {useState} from "react";
import {Link} from "react-router-dom";
import {useMutation,useQueryClient} from "@tanstack/react-query";
import {workflowApi} from "@/api/workflow";
import {usePlanningWindow} from "@/hooks/usePlanningWindow";
import {useSettings} from "@/hooks/useSettings";
import {Button} from "./ui/button";
export function ScheduleRecipe({recipeId}: {recipeId:string}) {
    const {window}=usePlanningWindow(); const [settings]=useSettings();
    const [date,setDate]=useState(window.start_date);const [mealType,setMealType]=useState("dinner");
    const [servings,setServings]=useState(settings.defaultServings); const qc=useQueryClient();
    const add=useMutation({mutationFn:workflowApi.schedule,onSuccess:()=>{
        qc.invalidateQueries({queryKey:["plans"]});qc.invalidateQueries({queryKey:["workflow"]});
        qc.invalidateQueries({queryKey:["prep-plan"]});qc.invalidateQueries({queryKey:["grocery"]});
    }});
    return <div className="space-y-3">
        <h2 className="font-semibold">Add to your meal prep plan</h2>
        <p className="text-sm text-gray-500">Schedule the portions you want to prepare. Shopping and prep will scale this recipe to match.</p>
        <form onSubmit={e=>{e.preventDefault();add.mutate({recipe_id:recipeId,date,meal_type:mealType,servings});}} className="flex flex-wrap gap-3 items-end">
            <label className="text-xs font-medium">Meal date<input required type="date" value={date} onChange={e=>{setDate(e.target.value);add.reset();}} className="block border rounded-lg p-2 mt-1 text-sm"/></label>
            <label className="text-xs font-medium">Meal<select value={mealType} onChange={e=>{setMealType(e.target.value);add.reset();}} className="block border rounded-lg p-2 mt-1 text-sm">{["breakfast","lunch","dinner","snack"].map(type=><option key={type} value={type}>{type}</option>)}</select></label>
            <label className="text-xs font-medium">Servings to prep<input required type="number" min={0.5} max={24} step={0.5} value={servings} onChange={e=>{setServings(Number(e.target.value));add.reset();}} className="block border rounded-lg p-2 mt-1 text-sm w-28"/></label>
            <Button type="submit" loading={add.isPending} disabled={add.isSuccess}>Add to plan</Button>
        </form>
        {add.isSuccess && <p role="status" className="text-sm text-primary-700">Added to your plan. <Link to="/" className="underline">Review selected meals</Link>{(date<window.start_date||date>window.end_date)&&" — adjust your planning dates to include this meal."}</p>}
        {add.error&&<p role="alert" className="text-sm text-red-600">{add.error.message}</p>}
    </div>;
}
