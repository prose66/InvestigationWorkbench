"use client";

import { useCallback, useState } from "react";
import { Upload, FileJson, FileSpreadsheet, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface FileDropzoneProps {
  file: File | null;
  onFileSelect: (file: File | null) => void;
  accept?: string;
  maxSize?: number; // in bytes
}

export function FileDropzone({
  file,
  onFileSelect,
  accept = ".json,.ndjson,.csv",
  maxSize = 50 * 1024 * 1024, // 50MB default
}: FileDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      setError(null);

      const droppedFile = e.dataTransfer.files[0];
      if (!droppedFile) return;

      validateAndSetFile(droppedFile);
    },
    [maxSize, onFileSelect]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setError(null);
      const selectedFile = e.target.files?.[0];
      if (!selectedFile) return;

      validateAndSetFile(selectedFile);
    },
    [maxSize, onFileSelect]
  );

  const validateAndSetFile = (selectedFile: File) => {
    // Check file size
    if (selectedFile.size > maxSize) {
      setError(`File too large. Maximum size is ${formatBytes(maxSize)}.`);
      return;
    }

    // Check file extension
    const ext = selectedFile.name.split(".").pop()?.toLowerCase();
    if (!["json", "ndjson", "csv"].includes(ext || "")) {
      setError("Unsupported file type. Please use .json, .ndjson, or .csv files.");
      return;
    }

    onFileSelect(selectedFile);
  };

  const clearFile = () => {
    onFileSelect(null);
    setError(null);
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split(".").pop()?.toLowerCase();
    if (ext === "csv") return FileSpreadsheet;
    return FileJson;
  };

  if (file) {
    const FileIcon = getFileIcon(file.name);
    return (
      <div className="metric-card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyan/10">
              <FileIcon className="w-5 h-5 text-cyan" />
            </div>
            <div>
              <p className="font-medium text-foreground">{file.name}</p>
              <p className="text-xs text-muted-foreground">
                {formatBytes(file.size)}
              </p>
            </div>
          </div>
          <button
            onClick={clearFile}
            className="p-2 rounded-lg hover:bg-secondary transition-colors"
            title="Remove file"
          >
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <label
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "flex flex-col items-center justify-center w-full h-48 rounded-xl cursor-pointer",
          "border-2 border-dashed transition-all duration-200",
          isDragging
            ? "border-cyan bg-cyan/5"
            : "border-border hover:border-cyan/50 hover:bg-secondary/30",
          error && "border-destructive"
        )}
      >
        <div className="flex flex-col items-center justify-center pt-5 pb-6">
          <div
            className={cn(
              "p-3 rounded-full mb-3",
              isDragging ? "bg-cyan/10" : "bg-secondary"
            )}
          >
            <Upload
              className={cn(
                "w-6 h-6",
                isDragging ? "text-cyan" : "text-muted-foreground"
              )}
            />
          </div>
          <p className="mb-2 text-sm text-foreground">
            <span className="font-semibold">Click to upload</span> or drag and
            drop
          </p>
          <p className="text-xs text-muted-foreground">
            JSON, NDJSON, or CSV files (max {formatBytes(maxSize)})
          </p>
        </div>
        <input
          type="file"
          className="hidden"
          accept={accept}
          onChange={handleFileInput}
        />
      </label>
      {error && (
        <p className="mt-2 text-sm text-destructive flex items-center gap-2">
          <X className="w-4 h-4" />
          {error}
        </p>
      )}
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}
