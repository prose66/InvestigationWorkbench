"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Clock,
  Users,
  Network,
  Bookmark,
  Search,
  ArrowLeft,
  Shield,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarProps {
  caseId: string;
}

const navigation = [
  { name: "Overview", href: "", icon: LayoutDashboard },
  { name: "Timeline", href: "/timeline", icon: Clock },
  { name: "Entity", href: "/entity", icon: Users },
  { name: "Graph", href: "/graph", icon: Network },
  { name: "Bookmarks", href: "/bookmarks", icon: Bookmark },
];

export function Sidebar({ caseId }: SidebarProps) {
  const pathname = usePathname();
  const basePath = `/cases/${caseId}`;

  return (
    <div className="flex flex-col w-64 bg-gradient-to-b from-[hsl(220_20%_9%)] to-[hsl(220_20%_7%)] border-r border-border/50">
      {/* Header */}
      <div className="p-4 border-b border-border/50">
        <Link
          href="/"
          className="flex items-center text-sm text-muted-foreground hover:text-cyan transition-colors duration-200"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          All Cases
        </Link>

        {/* Case ID with branding */}
        <div className="mt-3 flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-cyan/10 pulse-glow">
            <Shield className="w-4 h-4 text-cyan" />
          </div>
          <div>
            <h2
              className="font-semibold text-foreground truncate max-w-[180px]"
              title={caseId}
            >
              {caseId}
            </h2>
            <p className="text-xs text-muted-foreground">Investigation Case</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3">
        <p className="px-3 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Navigation
        </p>
        <ul className="space-y-1">
          {navigation.map((item, index) => {
            const href = `${basePath}${item.href}`;
            const isActive =
              item.href === ""
                ? pathname === basePath
                : pathname.startsWith(href);

            return (
              <li
                key={item.name}
                className="fade-in-up"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <Link
                  href={href}
                  className={cn(
                    "nav-link",
                    isActive && "nav-link-active"
                  )}
                >
                  <item.icon
                    className={cn(
                      "w-4 h-4",
                      isActive && "text-cyan"
                    )}
                  />
                  {item.name}
                  {isActive && (
                    <Zap className="w-3 h-3 ml-auto text-amber-400" />
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Search (bottom) */}
      <div className="p-3 border-t border-border/50">
        <Link
          href={`${basePath}/search`}
          className={cn(
            "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm",
            "bg-secondary/30 border border-border/50",
            "text-muted-foreground hover:text-foreground hover:bg-secondary hover:border-cyan/30",
            "transition-all duration-200"
          )}
        >
          <Search className="w-4 h-4" />
          Search Events
        </Link>
      </div>

      {/* Footer accent */}
      <div className="h-1 bg-gradient-to-r from-transparent via-cyan/30 to-transparent" />
    </div>
  );
}
