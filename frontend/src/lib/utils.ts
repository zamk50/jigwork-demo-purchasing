import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Tailwind のクラスをまとめる(shadcn/ui の決まりの形)。 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
