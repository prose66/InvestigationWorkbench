"use client";

import { useParams } from "next/navigation";
import { useEffect } from "react";
import { Upload } from "lucide-react";
import { IngestWizard } from "@/components/ingest";
import { useIngestStore } from "@/stores/ingestStore";

export default function IngestPage() {
  const params = useParams();
  const caseId = params.caseId as string;
  const reset = useIngestStore((state) => state.reset);

  // Reset wizard state when navigating to this page
  useEffect(() => {
    reset();
  }, [caseId, reset]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-cyan/10 pulse-glow">
          <Upload className="w-5 h-5 text-cyan" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Ingest Data</h1>
          <p className="text-muted-foreground text-sm">
            Import log files and map fields to the unified schema
          </p>
        </div>
      </div>

      {/* Wizard */}
      <IngestWizard caseId={caseId} />
    </div>
  );
}
