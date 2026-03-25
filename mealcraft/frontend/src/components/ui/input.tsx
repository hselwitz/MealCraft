import React from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
    hint?: string;
}

export function Input({label, error, hint, className = "", id, ...props}: InputProps) {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
    return (
        <div className="flex flex-col gap-1">
            {label && (
                <label htmlFor={inputId} className="text-sm font-medium text-gray-700">
                    {label}
                </label>
            )}
            <input
                id={inputId}
                className={[
                    "w-full rounded-lg border px-3 py-2 text-sm",
                    "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent",
                    "placeholder:text-gray-400",
                    error ? "border-red-400 bg-red-50" : "border-gray-300 bg-white",
                    className,
                ].join(" ")}
                {...props}
            />
            {error && <p className="text-xs text-red-600">{error}</p>}
            {hint && !error && <p className="text-xs text-gray-500">{hint}</p>}
        </div>
    );
}
