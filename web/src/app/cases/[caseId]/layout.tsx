"use client";

import { useEffect } from "react";
import { useParams } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { PivotChain } from "@/components/entity/PivotChain";
import { useCaseStore } from "@/stores/caseStore";
import { usePivotStore } from "@/stores/pivotStore";

export default function CaseLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams();
  const caseId = params.caseId as string;
  const { setSelectedCaseId } = useCaseStore();
  const { setCaseId } = usePivotStore();

  useEffect(() => {
    setSelectedCaseId(caseId);
    setCaseId(caseId);
  }, [caseId, setSelectedCaseId, setCaseId]);

  return (
    <div className="flex h-screen bg-background">
      <Sidebar caseId={caseId} />
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Pivot Chain Bar */}
        <PivotChain className="mx-4 mt-4" />
        {/* Page Content */}
        <div className="flex-1 overflow-auto p-4">{children}</div>
      </main>
    </div>
  );
}
