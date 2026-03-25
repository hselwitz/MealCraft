import {apiGet, apiPut} from "./client";
import type {AppSettings} from "@/hooks/useSettings";

export const settingsApi = {
    get: () => apiGet<AppSettings>("/settings"),
    update: (body: AppSettings) => apiPut<AppSettings>("/settings", body),
};
