import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Header() {
  return (
    <header className="border-b border-black/10 bg-white">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        {/* Logo / Tittel */}
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-[rgb(var(--nmbu-primary))]" />
          <div className="leading-tight">
            <div className="text-sm font-semibold">
              NMBU
            </div>
            <div className="text-xs text-black/60">
              Studieveiledning
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
