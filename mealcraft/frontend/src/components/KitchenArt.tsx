/** Small decorative kitchen sketches, drawn as vectors so they stay crisp. */
export function KitchenArt({variant = "prep", className = ""}: {variant?: "prep" | "shop" | "discover"; className?: string}) {
    return <svg aria-hidden="true" focusable="false" viewBox="0 0 240 170" className={className} fill="none">
        <ellipse cx="126" cy="144" rx="95" ry="12" fill="#e8e3d6"/>
        {variant === "shop" ? <>
            <path d="M61 68h117l-11 74H73L61 68Z" fill="#e8cf9e" stroke="#b99359" strokeWidth="2"/>
            <path d="M91 75V55a28 28 0 0 1 56 0v20" stroke="#b99359" strokeWidth="5" strokeLinecap="round"/>
            <path d="m72 68-8-36 12-5 17 41" fill="#dfb981" stroke="#b99359" strokeWidth="2"/>
            <path d="m69 41 9-3m-6 14 10-3" stroke="#b99359" strokeWidth="2"/>
            <path d="M142 69c-14-24-8-39 5-35 6-19 23-17 24-3 20-6 27 8 15 19 12 12 1 25-16 17" fill="#70966a"/>
            <path d="m157 73 8-35" stroke="#456849" strokeWidth="3" strokeLinecap="round"/>
            <path d="M99 85h43m-50 15h57m-56 15h48" stroke="#c6a16a" strokeWidth="2" strokeLinecap="round"/>
        </> : variant === "discover" ? <>
            <ellipse cx="120" cy="89" rx="72" ry="57" fill="#fffdf7" stroke="#c8ceba" strokeWidth="2"/>
            <ellipse cx="120" cy="89" rx="56" ry="43" stroke="#e3e7d7" strokeWidth="2"/>
            <path d="M88 89c-15-24 17-39 31-18 17-19 42-1 31 19-5 12-25 28-34 28-9 0-22-15-28-29Z" fill="#dba781"/>
            <path d="m93 88 13 7m16-17 9 9m-15 17 9 5" stroke="#b9805b" strokeWidth="3" strokeLinecap="round"/>
            <path d="M87 66c-20-4-19-20-19-20 19-2 26 6 19 20Zm54 48c5 18 22 18 22 18 2-18-7-26-22-18Z" fill="#70966a"/>
            <path d="M209 53v74m-8-74v20c0 10 16 10 16 0V53M29 53v74M22 53v20h14V53" stroke="#87927a" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
        </> : <>
            <g transform="rotate(-7 85 78)">
                <rect x="29" y="35" width="107" height="82" rx="16" fill="#fffdf7" stroke="#a7b394" strokeWidth="2"/>
                <rect x="37" y="43" width="91" height="66" rx="11" fill="#f2eddc"/>
                <path d="M85 44v64" stroke="#d9d3bd" strokeWidth="2"/>
                <path d="M47 65c12-20 32-10 29 9-2 16-19 27-29 13-4-6-4-15 0-22Z" fill="#dba781"/>
                <path d="m51 69 12 8m-13 7 10 6" stroke="#b9805b" strokeWidth="2" strokeLinecap="round"/>
                <path d="m97 60 8 3m7 10-8 3m-11 8 8 3m11 10-8-2m-8-24 7-1" stroke="#d6c499" strokeWidth="4" strokeLinecap="round"/>
            </g>
            <g transform="rotate(7 154 111)">
                <rect x="100" y="72" width="109" height="68" rx="15" fill="#fffdf7" stroke="#a7b394" strokeWidth="2"/>
                <rect x="108" y="80" width="93" height="52" rx="10" fill="#edf1e3"/>
                <path d="M150 81v50" stroke="#cdd7ba" strokeWidth="2"/>
                <path d="M120 95c-12 2-10 16 0 16 4 13 17 9 16 0 12-4 8-17-2-16-4-10-15-8-14 0Z" fill="#70966a"/>
                <path d="m126 101 3 19" stroke="#456849" strokeWidth="2" strokeLinecap="round"/>
                <path d="m164 94 15 4m-18 9 19 5m-15 9 15-2" stroke="#dba781" strokeWidth="7" strokeLinecap="round"/>
            </g>
        </>}
        <path d="m192 26 2 7 7 2-7 2-2 7-2-7-7-2 7-2 2-7Z" fill="#c9a666"/>
        <circle cx="42" cy="131" r="3" fill="#c9a666"/>
    </svg>;
}
