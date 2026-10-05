"use client";
import { useCallback, useEffect, useState } from "react";
import { initialQuality, type QualityLevel, type TextSize, type ThemeName } from "./explorerTheme";

const KEY = "explorer.settings.v1";
interface Stored {
  theme?: ThemeName;
  text?: TextSize;
}
function read(): Stored {
  try {
    return JSON.parse(window.localStorage.getItem(KEY) ?? "{}") as Stored;
  } catch {
    return {};
  }
}

/** Theme (dark default / projector), text size and quality. Stored in localStorage when available; always optional. */
export function useExplorerSettings(urlQuality: string | null) {
  const [theme, setThemeState] = useState<ThemeName>("dark");
  const [text, setTextState] = useState<TextSize>("normal");
  const [quality, setQuality] = useState<QualityLevel>("high");
  const [auto, setAuto] = useState(true);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const s = read();
    if (s.theme === "projector" || s.theme === "dark") setThemeState(s.theme);
    if (s.text === "large" || s.text === "normal") setTextState(s.text);
    const nav = navigator as Navigator & { deviceMemory?: number };
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (urlQuality === "high" || urlQuality === "medium" || urlQuality === "low") {
      setQuality(urlQuality);
      setAuto(false);
    } else {
      setQuality(initialQuality({ cores: nav.hardwareConcurrency, memory: nav.deviceMemory, width: window.innerWidth, reducedMotion: reduced }));
    }
    setReady(true);
  }, [urlQuality]);

  // apply to <html> so the whole page (header, panels) follows; removed again when the explorer unmounts
  useEffect(() => {
    const el = document.documentElement;
    el.dataset.theme = theme;
    el.dataset.text = text;
    return () => {
      delete el.dataset.theme;
      delete el.dataset.text;
    };
  }, [theme, text]);

  const save = (patch: Stored) => {
    try {
      window.localStorage.setItem(KEY, JSON.stringify({ ...read(), ...patch }));
    } catch {
      /* storage unavailable: the setting simply is not remembered */
    }
  };
  const setTheme = useCallback((t: ThemeName) => {
    setThemeState(t);
    save({ theme: t });
  }, []);
  const setText = useCallback((t: TextSize) => {
    setTextState(t);
    save({ text: t });
  }, []);
  return { theme, setTheme, text, setText, quality, setQuality, auto, setAuto, ready };
}
