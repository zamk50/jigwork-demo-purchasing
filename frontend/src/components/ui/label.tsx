import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

export function Label({ className, htmlFor, ...props }: ComponentProps<"label">) {
  return <label htmlFor={htmlFor} className={cn("text-sm font-medium", className)} {...props} />;
}
