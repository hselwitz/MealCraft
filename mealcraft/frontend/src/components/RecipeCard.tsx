import {useNavigate} from "react-router-dom";
import {Clock, Flame, Users} from "lucide-react";
import type {RecipeSummary} from "@/types";
import {Card, CardBody} from "./ui/card";
import {Badge} from "./ui/badge";

interface RecipeCardProps {
    recipe: RecipeSummary;
}

const difficultyVariant = {
    easy: "green" as const,
    medium: "yellow" as const,
    hard: "red" as const,
};

const difficultyStrip = {
    easy: "bg-green-400",
    medium: "bg-yellow-400",
    hard: "bg-red-400",
};

export function RecipeCard({recipe}: RecipeCardProps) {
    const navigate = useNavigate();

    return (
        <Card
            onClick={() => navigate(`/recipes/${recipe.id}`)}
            className="hover:shadow-md transition-shadow overflow-hidden cursor-pointer"
        >
            <div className={`h-1 ${difficultyStrip[recipe.difficulty] ?? "bg-gray-300"}`}/>
            <CardBody>
                <h3 className="font-semibold text-gray-900 line-clamp-2 mb-1">{recipe.title}</h3>
                <p className="text-sm text-gray-500 line-clamp-2 mb-2">{recipe.description}</p>

                <div className="flex items-center gap-3 text-xs text-gray-500 mb-2">
                    <div className="flex items-center gap-1">
                        <Clock size={12}/>
                        <span>{recipe.total_time_min}min</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <Users size={12}/>
                        <span>{recipe.servings} serv</span>
                    </div>
                    {recipe.calories_per_serving && (
                        <div className="flex items-center gap-1">
                            <Flame size={12}/>
                            <span>{recipe.calories_per_serving} cal</span>
                        </div>
                    )}
                </div>

                <div className="flex flex-wrap gap-1">
                    <Badge variant={difficultyVariant[recipe.difficulty] ?? "gray"}>
                        {recipe.difficulty}
                    </Badge>
                    {recipe.tags?.slice(0, 3).map((tag) => (
                        <Badge key={tag} variant="blue">
                            {tag}
                        </Badge>
                    ))}
                </div>
            </CardBody>
        </Card>
    );
}
