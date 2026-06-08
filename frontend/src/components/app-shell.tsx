"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Briefcase,
  FileText,
  Inbox,
  LayoutDashboard,
  LogOut,
  Sparkles,
} from "lucide-react";
import { clearToken, hasToken } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/applications", label: "Applications", icon: Briefcase },
  { href: "/profile", label: "Resume", icon: FileText },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    setAuthenticated(hasToken());
  }, [pathname]);

  function handleLogout() {
    clearToken();
    setAuthenticated(false);
    router.push("/");
  }

  if (!authenticated) {
    return <div className="min-h-screen">{children}</div>;
  }

  return (
    <div className="min-h-screen lg:flex">
      <aside className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col lg:border-b-0 lg:border-r">
        <div className="flex h-full flex-col">
          <div className="border-b border-zinc-800 px-5 py-5">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-zinc-700 bg-zinc-900">
                <Inbox className="h-4 w-4 text-zinc-200" />
              </div>
              <div>
                <p className="text-sm font-semibold tracking-tight text-zinc-50">AI Job Inbox</p>
                <p className="text-xs text-zinc-500">Portfolio demo</p>
              </div>
            </div>
            <div className="mt-4 flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2">
              <Sparkles className="h-3.5 w-3.5 text-zinc-400" />
              <div className="min-w-0">
                <p className="truncate text-xs font-medium text-zinc-300">Demo session</p>
                <p className="truncate text-[11px] text-zinc-500">JWT stored locally</p>
              </div>
            </div>
          </div>

          <nav className="flex-1 space-y-1 px-3 py-4">
            {navItems.map(({ href, label, icon: Icon }) => {
              const active =
                pathname === href || (href !== "/dashboard" && pathname.startsWith(`${href}/`));
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    active
                      ? "bg-zinc-100 text-zinc-950"
                      : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100",
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </Link>
              );
            })}
          </nav>

          <div className="border-t border-zinc-800 p-3">
            <Button variant="ghost" size="sm" className="w-full justify-start" onClick={handleLogout}>
              <LogOut className="h-4 w-4" />
              Clear token
            </Button>
          </div>
        </div>
      </aside>

      <div className="flex-1 lg:pl-64">
        <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">{children}</main>
      </div>
    </div>
  );
}
