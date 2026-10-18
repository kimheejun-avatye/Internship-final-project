import { post } from "./session-client";
export const changePassword = (current_password: string, new_password: string) => post<void>("/api/auth/password/change", { current_password, new_password }, true);
export const sendResetCode = (email: string) => post<{ message: string; cooldown_seconds: number; expires_in: number }>("/api/auth/password/reset/send-code", { email });
export const verifyResetCode = (email: string, code: string) => post<{ reset_token: string; expires_in: number }>("/api/auth/password/reset/verify-code", { email, code });
export const resetPassword = (reset_token: string, new_password: string) => post<void>("/api/auth/password/reset", { reset_token, new_password });
