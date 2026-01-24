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
    <div className="flex flex-col w-64 bg-card border-r">
      {/* Header */}
      <div className="p-4 border-b">
        <Link
          href="/"
          className="flex items-center text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          All Cases
        </Link>
        <h2 className="font-semibold mt-2 truncate" title={caseId}>
          {caseId}
        </h2>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {navigation.map((item) => {
            const href = `${basePath}${item.href}`;
            const isActive =
              item.href === ""
                ? pathname === basePath
                : pathname.startsWith(href);

            return (
              <li key={item.name}>
                <Link
                  href={href}
                  className={cn(
                    "flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <item.icon className="w-4 h-4 mr-3" />
                  {item.name}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Search (bottom) */}
      <div className="p-4 border-t">
        <Link
          href={`${basePath}/search`}
          className="flex items-center px-3 py-2 rounded-md text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <Search className="w-4 h-4 mr-3" />
          Search Events
        </Link>
      </div>
    </div>
  );
}
