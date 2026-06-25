"use client";

import { Moon, Sun } from "@phosphor-icons/react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { IconButton } from "./IconButton";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  if (!mounted) return <IconButton aria-label="theme" />;
  const dark = theme === "dark";
  return (
    <IconButton
      aria-label="切换主题"
      title="切换浅色/深色"
      onClick={() => setTheme(dark ? "light" : "dark")}
    >
      {dark ? <Sun size={18} /> : <Moon size={18} />}
    </IconButton>
  );
}
