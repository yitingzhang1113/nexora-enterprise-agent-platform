"use client";

import { ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "danger";

const styles: Record<Variant, string> = {
  primary: "bg-accent text-white hover:bg-accent-hover",
  secondary: "bg-bg-2 text-text-5 hover:bg-bg-3 border border-border",
  ghost: "bg-transparent text-text-3 hover:bg-bg-2",
  danger: "bg-danger text-white hover:opacity-90",
};

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

export const Button = forwardRef<HTMLButtonElement, Props>(
  ({ variant = "primary", className, ...rest }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md px-3.5 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed",
        styles[variant],
        className
      )}
      {...rest}
    />
  )
);
Button.displayName = "Button";
