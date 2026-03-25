import {useState, useEffect} from "react";

export function useLocalStorage<T>(key: string, initial: T) {
    const [value, setValue] = useState<T>(() => {
        try {
            const stored = localStorage.getItem(key);
            return stored ? (JSON.parse(stored) as T) : initial;
        } catch {
            return initial;
        }
    });

    useEffect(() => {
        try {
            if (value === null || value === undefined) {
                localStorage.removeItem(key);
            } else {
                localStorage.setItem(key, JSON.stringify(value));
            }
        } catch { /* ignore quota errors */ }
    }, [key, value]);

    return [value, setValue] as const;
}
