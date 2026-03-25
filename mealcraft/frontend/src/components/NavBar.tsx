import {NavLink} from "react-router-dom";
import {BookOpen, CalendarDays, ClipboardList, RefrigeratorIcon, Settings2, ShoppingCart} from "lucide-react";

const navItems = [
    {to: "/", label: "Planner", icon: CalendarDays},
    {to: "/grocery", label: "Grocery", icon: ShoppingCart},
    {to: "/prep", label: "Prep", icon: ClipboardList},
    {to: "/recipes", label: "Recipes", icon: BookOpen},
    {to: "/leftovers", label: "Leftovers", icon: RefrigeratorIcon},
    {to: "/settings", label: "Settings", icon: Settings2},
];

export function NavBar() {
    return (
        <>
            {/* ── Desktop top nav ── */}
            <nav
                className="hidden sm:block fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 shadow-sm">
                <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
                    <div className="flex items-center gap-2">
                        <span className="text-2xl">🍽</span>
                        <span className="font-bold text-lg text-primary-700">MealCraft</span>
                    </div>
                    <div className="flex items-center gap-1">
                        {navItems.map(({to, label, icon: Icon}) => (
                            <NavLink
                                key={to}
                                to={to}
                                end={to === "/"}
                                className={({isActive}) =>
                                    [
                                        "flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                                        isActive
                                            ? "bg-primary-50 text-primary-700"
                                            : "text-gray-600 hover:bg-gray-100 hover:text-gray-800",
                                    ].join(" ")
                                }
                            >
                                <Icon size={16}/>
                                {label}
                            </NavLink>
                        ))}
                    </div>
                </div>
            </nav>

            {/* ── Mobile top bar (logo only) ── */}
            <div
                className="sm:hidden fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 h-12 flex items-center px-4">
                <span className="text-xl mr-2">🍽</span>
                <span className="font-bold text-base text-primary-700">MealCraft</span>
            </div>

            {/* ── Mobile bottom tab bar ── */}
            <nav
                className="sm:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 safe-area-bottom">
                <div className="grid grid-cols-6 h-16">
                    {navItems.map(({to, label, icon: Icon}) => (
                        <NavLink
                            key={to}
                            to={to}
                            end={to === "/"}
                            className={({isActive}) =>
                                [
                                    "flex flex-col items-center justify-center gap-0.5 text-[10px] font-medium transition-colors",
                                    isActive ? "text-primary-600" : "text-gray-400",
                                ].join(" ")
                            }
                        >
                            <Icon size={20}/>
                            {label}
                        </NavLink>
                    ))}
                </div>
            </nav>
        </>
    );
}
