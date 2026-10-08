import {Link, NavLink} from "react-router-dom";
import {BookOpen, ChefHat, CalendarDays, ClipboardList, RefrigeratorIcon, Settings2, ShoppingCart, Sparkles} from "lucide-react";

const navItems = [
    {to: "/", label: "Plan", icon: CalendarDays},
    {to: "/grocery", label: "Shop", icon: ShoppingCart},
    {to: "/prep", label: "Prep", icon: ClipboardList},
    {to: "/discover", label: "Discover", icon: Sparkles},
    {to: "/repertoire", label: "Repertoire", icon: BookOpen},
];
function MoreTools() {
    return <details className="relative">
        <summary className="cursor-pointer px-3 py-2 text-sm text-gray-500 rounded-lg hover:bg-gray-100">More</summary>
        <div className="absolute right-0 top-full mt-1 w-44 bg-white border border-gray-200 rounded-xl shadow-lg p-2">
            {[{to: "/settings", label: "Settings", icon: Settings2}, {to: "/leftovers", label: "Leftovers", icon: RefrigeratorIcon}, {to: "/recipes", label: "All recipes", icon: BookOpen}].map(({to, label, icon: Icon}) => <Link key={to} to={to} onClick={(e) => e.currentTarget.closest("details")?.removeAttribute("open")} className="flex items-center gap-2 px-3 py-2 text-sm rounded-lg hover:bg-gray-50"><Icon size={16}/>{label}</Link>)}
        </div>
    </details>;
}
export function NavBar() {
    return <>
        <nav aria-label="Main navigation" className="hidden lg:block fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
                <Link to="/" className="flex items-center gap-2"><span className="brand-mark"><ChefHat size={20}/></span><span className="font-bold text-lg text-primary-700">MealCraft</span></Link>
                <div className="flex items-center gap-1">{navItems.map(({to, label, icon: Icon}) => <NavLink key={to} to={to} end={to === "/"} className={({isActive}) => `flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isActive ? "bg-primary-50 text-primary-700" : "text-gray-600 hover:bg-gray-100"}`}><Icon size={16}/>{label}</NavLink>)}<MoreTools/></div>
            </div>
        </nav>
        <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 h-12 flex items-center justify-between px-4">
            <Link to="/" className="flex items-center gap-2 font-bold text-base text-primary-700"><span className="brand-mark"><ChefHat size={20}/></span>MealCraft</Link><MoreTools/>
        </div>
        <nav aria-label="Mobile navigation" className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 safe-area-bottom">
            <div className="grid grid-cols-5 h-16">{navItems.map(({to, label, icon: Icon}) => <NavLink key={to} to={to} end={to === "/"} className={({isActive}) => `flex flex-col items-center justify-center gap-1 text-[10px] font-medium ${isActive ? "text-primary-600" : "text-gray-500"}`}><Icon size={20}/>{label}</NavLink>)}</div>
        </nav>
    </>;
}
