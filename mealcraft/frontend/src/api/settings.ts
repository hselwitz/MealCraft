import {apiGet, apiPut} from "./client";
import type {AppSettings} from "@/hooks/useSettings";

export const settingsApi = {
    get: () => apiGet<AppSettings>("/settings"),
    update: (body: Partial<AppSettings> & {openRouterApiKey?: string | null}) => apiPut<AppSettings>("/settings", body),
};
