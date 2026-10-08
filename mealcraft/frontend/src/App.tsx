import {BrowserRouter, Navigate, Route, Routes} from "react-router-dom";
import {PlanHome} from "./views/PlanHome";
import {PlanningWindowProvider} from "./hooks/usePlanningWindow";
import {NavBar} from "./components/NavBar";
import {Discover} from "./views/Discover";
import {Repertoire} from "./views/Repertoire";
import {WeeklyPlanner} from "./views/WeeklyPlanner";
import {RecipeDetail} from "./views/RecipeDetail";
import {PrepDashboard} from "./views/PrepDashboard";
import {GroceryList} from "./views/GroceryList";
import {LeftoverTracker} from "./views/LeftoverTracker";
import {RecipesList} from "./views/RecipesList";
import {Settings} from "./views/Settings";

export default function App() {
    return (
        <BrowserRouter>
            <PlanningWindowProvider>
            <div className="min-h-screen app-shell">
                <NavBar/>
                <main className="max-w-7xl mx-auto px-4 pt-16 lg:pt-20 pb-24 lg:pb-12">
                    <Routes>
                        <Route path="/" element={<PlanHome/>}/>
                        <Route path="/discover" element={<Discover/>}/>
                        <Route path="/planner" element={<WeeklyPlanner/>}/>
                        <Route path="/repertoire" element={<Repertoire/>}/>
                        <Route path="/prep" element={<PrepDashboard/>}/>
                        <Route path="/grocery" element={<GroceryList/>}/>
                        <Route path="/leftovers" element={<LeftoverTracker/>}/>
                        <Route path="/recipes" element={<RecipesList/>}/>
                        <Route path="/recipes/:id" element={<RecipeDetail/>}/>
                        <Route path="/settings" element={<Settings/>}/>
                        <Route path="*" element={<Navigate to="/" replace/>}/>
                    </Routes>
                </main>
            </div>
        </PlanningWindowProvider>
        </BrowserRouter>
    );
}
