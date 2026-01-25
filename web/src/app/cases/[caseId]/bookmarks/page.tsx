"use client";

import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getBookmarks, deleteBookmark, updateBookmark } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { useState } from "react";
import { Trash2, Edit2 } from "lucide-react";
import type { Bookmark } from "@/lib/types";

export default function BookmarksPage() {
  const params = useParams();
  const caseId = params.caseId as string;
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editLabel, setEditLabel] = useState("");
  const [editNotes, setEditNotes] = useState("");

  const { data: bookmarks, isLoading } = useQuery({
    queryKey: ["bookmarks", caseId],
    queryFn: () => getBookmarks(caseId),
  });

  const deleteMutation = useMutation({
    mutationFn: (bookmarkId: number) => deleteBookmark(caseId, bookmarkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookmarks", caseId] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      bookmarkId,
      label,
      notes,
    }: {
      bookmarkId: number;
      label: string;
      notes: string;
    }) => updateBookmark(caseId, bookmarkId, label, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookmarks", caseId] });
      setEditingId(null);
    },
  });

  const startEdit = (bookmark: Bookmark) => {
    setEditingId(bookmark.bookmark_id);
    setEditLabel(bookmark.label || "");
    setEditNotes(bookmark.notes || "");
  };

  const saveEdit = () => {
    if (editingId) {
      updateMutation.mutate({
        bookmarkId: editingId,
        label: editLabel,
        notes: editNotes,
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Bookmarks</h1>
      <p className="text-muted-foreground mb-6">
        Events you&apos;ve marked as important during your investigation
      </p>

      {!bookmarks || bookmarks.length === 0 ? (
        <div className="text-center py-12 bg-muted/50 rounded-lg">
          <p className="text-muted-foreground mb-2">No bookmarks yet</p>
          <p className="text-sm text-muted-foreground">
            Use the Timeline Explorer to bookmark important events
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {bookmarks.length} bookmarked event(s)
            </p>
          </div>

          <div className="border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="px-4 py-3 text-left">Time</th>
                  <th className="px-4 py-3 text-left">Source</th>
                  <th className="px-4 py-3 text-left">Type</th>
                  <th className="px-4 py-3 text-left">Host</th>
                  <th className="px-4 py-3 text-left">Label</th>
                  <th className="px-4 py-3 text-left">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {bookmarks.map((bookmark) => (
                  <tr key={bookmark.bookmark_id} className="hover:bg-muted/50">
                    <td className="px-4 py-3 whitespace-nowrap">
                      {bookmark.event_ts ? formatDate(bookmark.event_ts) : "-"}
                    </td>
                    <td className="px-4 py-3">{bookmark.source_system}</td>
                    <td className="px-4 py-3">{bookmark.event_type}</td>
                    <td className="px-4 py-3">{bookmark.host || "-"}</td>
                    <td className="px-4 py-3">
                      {editingId === bookmark.bookmark_id ? (
                        <input
                          type="text"
                          value={editLabel}
                          onChange={(e) => setEditLabel(e.target.value)}
                          className="w-full px-2 py-1 border rounded text-sm"
                          placeholder="Add label..."
                        />
                      ) : (
                        <span className="text-muted-foreground">
                          {bookmark.label || "No label"}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {editingId === bookmark.bookmark_id ? (
                          <>
                            <button
                              onClick={saveEdit}
                              disabled={updateMutation.isPending}
                              className="px-2 py-1 bg-primary text-primary-foreground rounded text-xs"
                            >
                              Save
                            </button>
                            <button
                              onClick={() => setEditingId(null)}
                              className="px-2 py-1 border rounded text-xs"
                            >
                              Cancel
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              onClick={() => startEdit(bookmark)}
                              className="p-1 hover:bg-muted rounded"
                              title="Edit"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() =>
                                deleteMutation.mutate(bookmark.bookmark_id)
                              }
                              disabled={deleteMutation.isPending}
                              className="p-1 hover:bg-destructive/10 rounded text-destructive"
                              title="Delete"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
