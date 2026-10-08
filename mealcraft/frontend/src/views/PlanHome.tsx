import {KitchenArt} from "@/components/KitchenArt";
import {Link} from "react-router-dom";
import {useQuery} from "@tanstack/react-query";
import {CalendarDays,ShoppingCart,ClipboardList,ArrowRight} from "lucide-react";
import {usePlans,usePlan,useRecipes,useDeleteSlot} from "@/hooks/useApi";
import {usePlanningWindow} from "@/hooks/usePlanningWindow";
import {workflowApi} from "@/api/workflow";
import {WorkflowBar} from "@/components/WorkflowBar";
import {ScheduleRecipe} from "@/components/ScheduleRecipe";
import {useState} from "react";
import {Button} from "@/components/ui/button";
export function PlanHome() {
    const {window,valid}=usePlanningWindow();const {data:plans}=usePlans();
    const active=plans?.find(p=>p.status==="active"||p.status==="draft");const {data:plan}=usePlan(active?.id);
    const summary=useQuery({queryKey:["workflow",active?.id,window],queryFn:()=>workflowApi.summary(active!.id,window),enabled:!!active&&valid});
    const {data:recipes}=useRecipes();const [recipeId,setRecipeId]=useState("");const remove=useDeleteSlot();
    const slots=plan?.slots.filter(s=>s.status==="planned"&&s.recipe&&s.date>=window.start_date&&s.date<=window.end_date).sort((a,b)=>a.date.localeCompare(b.date))??[];
    const next=!slots.length?{label:"Choose meals for your next prep",to:"/discover"}:!summary.data?.prep_ready?{label:"Coordinate your prep session",to:"/prep"}:!summary.data?.shop_ready?{label:"Build your combined shopping list",to:"/grocery"}:{label:"Open your prep checklist",to:"/prep"};
    return <div className="max-w-5xl mx-auto space-y-6">
        <header className="kitchen-hero"><div className="relative z-10 max-w-xl"><p className="text-xs font-semibold uppercase tracking-widest text-primary-700 mb-2">Plan once. Shop together. Prep efficiently.</p><h1 className="text-3xl sm:text-4xl kitchen-title">Your next meal prep</h1><p className="text-gray-500 mt-2">Choose a few meals you want to eat. Turn them into one shopping list and coordinated cooking sessions.</p></div><KitchenArt className="hidden sm:block w-44 lg:w-52 shrink-0"/></header>
        <WorkflowBar/>
        <div className="grid sm:grid-cols-3 gap-3">{[{to:"/",label:"Plan",icon:CalendarDays,value:`${summary.data?.meal_count??slots.length} meals · ${summary.data?.servings??0} servings`},{to:"/grocery",label:"Shop",icon:ShoppingCart,value:summary.data?.shop_ready?"Shopping list ready":"Build a combined list"},{to:"/prep",label:"Prep",icon:ClipboardList,value:summary.data?.prep_ready?`${summary.data.prep?.total_active_min} min hands-on` : "Coordinate selected meals"}].map(({to,label,icon:Icon,value})=><Link to={to} key={label} className="workflow-card"><span className="inline-flex p-2 rounded-xl bg-primary-50 text-primary-700 mb-3"><Icon size={20}/></span><h2 className="font-semibold">{label}</h2><p className="text-sm text-gray-500 mt-1">{value}</p></Link>)}</div>
        <Link to={next.to} className="flex justify-between gap-3 rounded-xl bg-primary-50 border border-primary-200 p-4 text-primary-900 font-semibold">{next.label}<ArrowRight size={20}/></Link>
        {summary.error&&<p role="alert" className="text-red-600 text-sm">{summary.error.message}</p>}
        <section className="space-y-3"><div className="flex justify-between"><h2 className="text-xl font-bold">Selected meals</h2><Link to="/planner" className="text-sm text-primary-700">Open calendar</Link></div>
            {!slots.length&&<p className="rounded-xl border border-dashed p-6 text-gray-500 text-sm">No recipes scheduled for these dates. Choose saved recipes below or <Link to="/discover" className="underline text-primary-700">find easy variations</Link>.</p>}
            {slots.map(slot=><div key={slot.id} className="flex flex-wrap items-center gap-3 bg-white border rounded-xl p-4"><div className="flex-1 min-w-40"><Link to={`/recipes/${slot.recipe_id}`} className="font-semibold">{slot.recipe!.title}</Link><p className="text-xs text-gray-500 mt-1">{new Date(slot.date+"T12:00:00").toLocaleDateString(undefined,{weekday:"short",month:"short",day:"numeric"})} · {slot.meal_type} · {slot.servings} servings</p></div><Button size="sm" variant="ghost" loading={remove.isPending&&remove.variables?.slotId===slot.id} onClick={()=>remove.mutate({planId:active!.id,slotId:slot.id})}>Remove from plan</Button></div>)}
            {!!summary.data?.shared_ingredients.length&&<p className="text-sm text-primary-800 bg-primary-50 rounded-lg p-3">Shared ingredients to prep together: {summary.data.shared_ingredients.join(", ")}.</p>}
        </section>
        <section className="bg-white border rounded-xl p-5 space-y-4"><h2 className="text-lg font-semibold">Add an existing recipe</h2><select aria-label="Choose a recipe" value={recipeId} onChange={e=>setRecipeId(e.target.value)} className="border rounded-lg p-3 w-full text-sm"><option value="">Choose from your recipe library…</option>{recipes?.map(recipe=><option key={recipe.id} value={recipe.id}>{recipe.title}</option>)}</select>{recipeId&&<ScheduleRecipe key={recipeId} recipeId={recipeId}/>}<div className="flex flex-wrap gap-4 text-sm text-primary-700"><Link to="/repertoire">Browse repertoire</Link><Link to="/discover">Discover convenient meals</Link></div></section>
        {summary.data?.prep_ready&&summary.data.prep?.shared_components?.length?<section className="rounded-xl bg-white border p-5"><h2 className="font-semibold">Your shared prep</h2><p className="text-sm text-gray-600 mt-2">{summary.data.prep.shared_components.join(" · ")}</p><p className="text-sm text-gray-500 mt-2">Estimated session: {summary.data.prep.session_elapsed_min} minutes elapsed · {summary.data.prep.total_active_min} minutes hands-on.</p></section>:null}
    </div>;
}
