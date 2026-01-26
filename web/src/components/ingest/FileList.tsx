"use client";

import { useRef, useState, useCallback } from "react";
import { Upload, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { useIngestStore } from "@/stores/ingestStore";
import { FileCard } from "./FileCard";

interface FileListProps {
  onPreviewAll: () => void;
  isPreviewingAll: boolean;
}

export function FileList({ onPreviewAll, isPreviewingAll }: FileListProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const {
    files,
    addFile,
    removeFile,
    updateFileSource,
    updateFileQueryName,
  } = useIngestStore();

  const handleFiles = useCallback(
    (fileList: FileList | null) => {
      if (!fileList) return;
      for (let i = 0; i < fileList.length; i++) {
        const file = fileList[i];
        // Accept JSON, NDJSON, CSV, and text files
        if (
          file.type === "application/json" ||
          file.type === "text/csv" ||
          file.type === "text/plain" ||
          file.name.endsWith(".json") ||
          file.name.endsWith(".ndjson") ||
          file.name.endsWith(".csv") ||
          file.name.endsWith(".txt") ||
          file.name.endsWith(".log")
        ) {
          addFile(file);
        }
      }
    },
    [addFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragActive(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      handleFiles(e.target.files);
      // Reset input so same file can be selected again
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    },
    [handleFiles]
  );

  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  const allFilesHavePreview = files.every((f) => f.previewData !== null);
  const anyFileLoading = files.some((f) => f.isLoading);
  const validFiles = files.filter((f) => f.source.trim() && f.queryName.trim());

  return (
    <div className="space-y-4">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".json,.ndjson,.csv,.txt,.log,application/json,text/csv,text/plain"
        onChange={handleInputChange}
        className="hidden"
      />

      {/* Dropzone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={files.length === 0 ? openFilePicker : undefined}
        className={cn(
          "border-2 border-dashed rounded-lg p-6 transition-colors",
          isDragActive
            ? "border-cyan bg-cyan/5"
            : files.length === 0
            ? "border-border hover:border-cyan/50 cursor-pointer"
            : "border-border"
        )}
      >
        {files.length === 0 ? (
          <div className="flex flex-col items-center justify-center text-center py-8">
            <div className="w-12 h-12 rounded-full bg-cyan/10 flex items-center justify-center mb-4">
              <Upload className="w-6 h-6 text-cyan" />
            </div>
            <p className="text-foreground font-medium mb-1">
              Drop files here or click to browse
            </p>
            <p className="text-sm text-muted-foreground">
              Supports JSON, NDJSON, and CSV files
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {/* File cards */}
            {files.map((entry, index) => (
              <FileCard
                key={entry.id}
                entry={entry}
                index={index}
                onRemove={() => removeFile(entry.id)}
                onSourceChange={(source) => updateFileSource(entry.id, source)}
                onQueryNameChange={(name) => updateFileQueryName(entry.id, name)}
              />
            ))}

            {/* Add more files button */}
            <button
              type="button"
              onClick={openFilePicker}
              className="w-full py-3 border-2 border-dashed border-border rounded-lg text-muted-foreground hover:text-foreground hover:border-cyan/50 transition-colors flex items-center justify-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add more files
            </button>
          </div>
        )}
      </div>

      {/* Summary and preview button */}
      {files.length > 0 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            <span className="text-foreground font-medium">{files.length}</span>{" "}
            file{files.length !== 1 && "s"} selected
            {validFiles.length < files.length && (
              <span className="text-amber-500 ml-2">
                ({files.length - validFiles.length} missing required fields)
              </span>
            )}
          </div>

          {!allFilesHavePreview && (
            <button
              onClick={onPreviewAll}
              disabled={validFiles.length === 0 || anyFileLoading}
              className={cn(
                "px-4 py-2 rounded-lg font-medium transition-colors",
                validFiles.length > 0 && !anyFileLoading
                  ? "bg-cyan text-background hover:bg-cyan/90"
                  : "bg-secondary text-muted-foreground cursor-not-allowed"
              )}
            >
              {anyFileLoading
                ? "Processing..."
                : `Preview ${validFiles.length === files.length ? "All" : validFiles.length} File${validFiles.length !== 1 ? "s" : ""}`}
            </button>
          )}

          {allFilesHavePreview && (
            <div className="flex items-center gap-2 text-emerald-500 text-sm">
              <span>All files previewed</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
