import {NavLink} from "react-router-dom";
import {usePlanningWindow} from "@/hooks/usePlanningWindow";
export function WorkflowBar() {
    const {window,setWindow,valid}=usePlanningWindow();
    return <div className="rounded-xl border border-gray-200 bg-white/90 p-4 space-y-3">
        <div className="flex gap-2 text-sm font-semibold">{[["/","Plan"],["/grocery","Shop"],["/prep","Prep"]].map(([to,label],index)=><NavLink key={to} to={to} end aria-label={`${index+1} · ${label}`} className={({isActive})=>`inline-flex items-center gap-2 rounded-lg px-3 py-2 transition-colors ${isActive?"bg-primary-50 text-primary-700":"text-gray-500 hover:bg-gray-50 hover:text-primary-700"}`}><span className="flex h-5 w-5 items-center justify-center rounded-full border border-current text-[10px]">{index+1}</span>{label}</NavLink>)}</div>
        <div className="flex flex-wrap gap-3 items-end">
            <label className="text-xs font-medium text-gray-600">Meals from<input aria-label="Meals from" type="date" value={window.start_date} onChange={e=>setWindow({...window,start_date:e.target.value})} className="block border rounded-lg p-2 mt-1 text-sm"/></label>
            <label className="text-xs font-medium text-gray-600">Through<input aria-label="Meals through" type="date" value={window.end_date} onChange={e=>setWindow({...window,end_date:e.target.value})} className="block border rounded-lg p-2 mt-1 text-sm"/></label>
            <p className="text-xs text-gray-500 pb-2">One date range for your plan, shopping list, and prep session.</p>
        </div>
        {!valid && <p role="alert" className="text-xs text-red-600">Choose an ordered date range of up to 31 days.</p>}
    </div>;
}
