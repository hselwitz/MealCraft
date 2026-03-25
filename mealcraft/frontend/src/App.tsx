import {BrowserRouter, Navigate, Route, Routes} from "react-router-dom";
import {NavBar} from "./components/NavBar";
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
            <div className="min-h-screen bg-gray-50">
                <NavBar/>
                <main className="max-w-7xl mx-auto px-4 pt-16 sm:pt-20 pb-24 sm:pb-12">
                    <Routes>
                        <Route path="/" element={<WeeklyPlanner/>}/>
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
        </BrowserRouter>
    );
}
