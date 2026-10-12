import { http } from "./http";
import type { RegisterPayload, Token, UserOut } from "../types/api";

export async function register(payload: RegisterPayload): Promise<UserOut> {
  const { data } = await http.post<UserOut>("/auth/register", payload);
  return data;
}

export async function login(email: string, password: string): Promise<Token> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  const { data } = await http.post<Token>("/auth/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

export async function me(): Promise<UserOut> {
  const { data } = await http.get<UserOut>("/auth/me");
  return data;
}
