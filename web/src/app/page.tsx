"use client";

import Link from "next/link";
import { useCases } from "@/hooks/useCases";
import { useCaseStore } from "@/stores/caseStore";

export default function HomePage() {
  const { data: cases, isLoading, error } = useCases();
  const { setSelectedCaseId } = useCaseStore();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-destructive mb-2">Error</h1>
          <p className="text-muted-foreground">
            Failed to load cases. Is the API server running?
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            Run: <code className="bg-muted px-2 py-1 rounded">make api</code>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold">Investigation Workbench</h1>
          <p className="text-muted-foreground mt-1">
            Security investigation and analysis platform
          </p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <h2 className="text-xl font-semibold mb-4">Select a Case</h2>

        {!cases || cases.length === 0 ? (
          <div className="text-center py-12 bg-muted/50 rounded-lg">
            <p className="text-muted-foreground mb-2">No cases found</p>
            <p className="text-sm text-muted-foreground">
              Create a case using:{" "}
              <code className="bg-muted px-2 py-1 rounded">
                python -m cli init-case &lt;case_id&gt;
              </code>
            </p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {cases.map((c) => (
              <Link
                key={c.case_id}
                href={`/cases/${c.case_id}`}
                onClick={() => setSelectedCaseId(c.case_id)}
                className="block p-6 bg-card border rounded-lg hover:shadow-md transition-shadow"
              >
                <h3 className="font-semibold text-lg">{c.case_id}</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Click to view case details
                </p>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
