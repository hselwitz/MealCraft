import {createContext, useContext} from "react";
import {useLocalStorage} from "./useLocalStorage";
export interface PlanningWindow {start_date: string; end_date: string}
export function localDate(date = new Date()) {return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,"0")}-${String(date.getDate()).padStart(2,"0")}`;}
const Context = createContext<{window: PlanningWindow; setWindow: (window: PlanningWindow) => void; valid: boolean} | null>(null);
export function PlanningWindowProvider({children}: {children: React.ReactNode}) {
    const end = new Date(); end.setDate(end.getDate()+6);
    const [window, setWindow] = useLocalStorage<PlanningWindow>("mealcraft-planning-window", {start_date: localDate(), end_date: localDate(end)});
    const days = (new Date(window.end_date).getTime()-new Date(window.start_date).getTime())/86400000;
    return <Context.Provider value={{window,setWindow,valid: days >= 0 && days <= 30}}>{children}</Context.Provider>;
}
export function usePlanningWindow() {const context=useContext(Context); if(!context) throw Error("Planning window provider missing");return context;}
