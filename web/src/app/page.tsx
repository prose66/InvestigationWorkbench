"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { Plus, Trash2, X, FolderPlus } from "lucide-react";
import { useCases, useCreateCase, useDeleteCase } from "@/hooks/useCases";
import { useCaseStore } from "@/stores/caseStore";

export default function HomePage() {
  const { data: cases, isLoading, error } = useCases();
  const { setSelectedCaseId } = useCaseStore();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

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
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Select a Case</h2>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium"
          >
            <Plus className="w-4 h-4" />
            New Case
          </button>
        </div>

        {!cases || cases.length === 0 ? (
          <div className="text-center py-12 bg-muted/50 rounded-lg">
            <FolderPlus className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground mb-4">No cases found</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium"
            >
              <Plus className="w-4 h-4" />
              Create Your First Case
            </button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {cases.map((c) => (
              <CaseCard
                key={c.case_id}
                caseId={c.case_id}
                onSelect={() => setSelectedCaseId(c.case_id)}
                onDeleteRequest={() => setDeleteConfirm(c.case_id)}
              />
            ))}
          </div>
        )}
      </main>

      {showCreateModal && (
        <CreateCaseModal onClose={() => setShowCreateModal(false)} />
      )}

      {deleteConfirm && (
        <DeleteConfirmModal
          caseId={deleteConfirm}
          onClose={() => setDeleteConfirm(null)}
        />
      )}
    </div>
  );
}

function CaseCard({
  caseId,
  onSelect,
  onDeleteRequest,
}: {
  caseId: string;
  onSelect: () => void;
  onDeleteRequest: () => void;
}) {
  return (
    <div className="relative group p-6 bg-card border rounded-lg hover:shadow-md transition-shadow">
      <Link
        href={`/cases/${caseId}`}
        onClick={onSelect}
        className="block"
      >
        <h3 className="font-semibold text-lg pr-8">{caseId}</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Click to view case details
        </p>
      </Link>
      <button
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          onDeleteRequest();
        }}
        className="absolute top-4 right-4 p-2 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 opacity-0 group-hover:opacity-100 transition-all"
        aria-label={`Delete case ${caseId}`}
      >
        <Trash2 className="w-4 h-4" />
      </button>
    </div>
  );
}

function CreateCaseModal({ onClose }: { onClose: () => void }) {
  const [caseId, setCaseId] = useState("");
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const createCase = useCreateCase();

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedId = caseId.trim();
    if (!trimmedId) {
      setError("Case ID is required");
      return;
    }

    if (!/^[a-zA-Z0-9_-]+$/.test(trimmedId)) {
      setError("Case ID can only contain letters, numbers, hyphens, and underscores");
      return;
    }

    try {
      await createCase.mutateAsync({ caseId: trimmedId, title: title.trim() || undefined });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create case");
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-card border rounded-lg shadow-xl w-full max-w-md m-4"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-case-title"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 id="create-case-title" className="font-semibold text-lg">Create New Case</h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label htmlFor="case-id" className="block text-sm font-medium mb-1.5">
              Case ID <span className="text-destructive">*</span>
            </label>
            <input
              ref={inputRef}
              id="case-id"
              type="text"
              value={caseId}
              onChange={(e) => setCaseId(e.target.value)}
              placeholder="incident-2024-001"
              className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
              autoComplete="off"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Letters, numbers, hyphens, and underscores only
            </p>
          </div>

          <div>
            <label htmlFor="case-title" className="block text-sm font-medium mb-1.5">
              Title <span className="text-muted-foreground">(optional)</span>
            </label>
            <input
              id="case-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Suspicious login activity investigation"
              className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          {error && (
            <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-lg">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createCase.isPending}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium disabled:opacity-50"
            >
              {createCase.isPending ? "Creating..." : "Create Case"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function DeleteConfirmModal({
  caseId,
  onClose,
}: {
  caseId: string;
  onClose: () => void;
}) {
  const deleteCase = useDeleteCase();
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    setError(null);
    try {
      await deleteCase.mutateAsync(caseId);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete case");
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-card border rounded-lg shadow-xl w-full max-w-md m-4"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="delete-case-title"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 id="delete-case-title" className="font-semibold text-lg text-destructive">
            Delete Case
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <p className="text-muted-foreground">
            Are you sure you want to delete case{" "}
            <span className="font-semibold text-foreground">{caseId}</span>?
          </p>
          <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-lg">
            This action cannot be undone. All data, events, and files associated with this case will be permanently deleted.
          </p>

          {error && (
            <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-lg">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleDelete}
              disabled={deleteCase.isPending}
              className="px-4 py-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 transition-colors font-medium disabled:opacity-50"
            >
              {deleteCase.isPending ? "Deleting..." : "Delete Case"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
