import { createContext, useContext } from "react";
import en from "./en.json";
import zh from "./zh.json";
import ja from "./ja.json";

const translations = { en, zh, ja };
const LangContext = createContext("en");

export function LangProvider({ lang, children }) {
  return <LangContext.Provider value={lang}>{children}</LangContext.Provider>;
}

export function useTranslation() {
  const lang = useContext(LangContext);
  const t = translations[lang] || translations.en;

  function get(path) {
    return path.split(".").reduce((obj, key) => obj?.[key], t) ?? path;
  }

  return { t: get, lang };
}

export function getLangFromPath(pathname) {
  if (pathname.startsWith("/zh")) return "zh";
  if (pathname.startsWith("/ja")) return "ja";
  return "en";
}

export function langPrefix(lang) {
  if (lang === "en") return "";
  return `/${lang}`;
}

export const LANGS = [
  { code: "en", label: "EN", name: "English" },
  { code: "zh", label: "\u4e2d\u6587", name: "\u4e2d\u6587" },
  { code: "ja", label: "\u65e5\u672c\u8a9e", name: "\u65e5\u672c\u8a9e" },
];
