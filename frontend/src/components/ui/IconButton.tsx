"use client";

import { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export function IconButton({
  className,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cn(
        "inline-flex h-8 w-8 items-center justify-center rounded-md text-text-3 transition-colors hover:bg-bg-2 hover:text-text-5",
        className
      )}
      {...rest}
    />
  );
}
