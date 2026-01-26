"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useIngestStore } from "@/stores/ingestStore";
import { uploadPreview, batchCommit } from "@/lib/api";

import { WizardSteps } from "./WizardSteps";
import { FileList } from "./FileList";
import { SchemaView } from "./SchemaView";
import { FieldMappingTable } from "./FieldMappingTable";
import { EntityFieldSelector } from "./EntityFieldSelector";
import { IngestSummary } from "./IngestSummary";
import { IngestProgress } from "./IngestProgress";

interface IngestWizardProps {
  caseId: string;
}

export function IngestWizard({ caseId }: IngestWizardProps) {
  const router = useRouter();
  const [isPreviewingAll, setIsPreviewingAll] = useState(false);

  const {
    step,
    files,
    workingSchema,
    fieldMappings,
    entityFields,
    saveMapper,
    timeStart,
    timeEnd,
    isIngesting,
    setFileLoading,
    setFilePreview,
    setFileError,
    buildMergedSchema,
    updateMapping,
    toggleEntityField,
    setSaveMapper,
    setTimeStart,
    setTimeEnd,
    setResult,
    setIngesting,
    setIngestError,
    setCurrentIngestIndex,
    nextStep,
    prevStep,
    goToStep,
    reset,
    canProceed,
    getMappingsArray,
  } = useIngestStore();

  // Handle preview all files
  const handlePreviewAll = async () => {
    setIsPreviewingAll(true);

    const validFiles = files.filter(
      (f) => f.source.trim() && f.queryName.trim() && !f.previewData
    );

    for (const fileEntry of validFiles) {
      setFileLoading(fileEntry.id, true);

      try {
        const content = await readFileAsBase64(fileEntry.file);
        const preview = await uploadPreview(
          caseId,
          fileEntry.source,
          content,
          fileEntry.file.name
        );
        setFilePreview(fileEntry.id, preview);
      } catch (err) {
        setFileError(
          fileEntry.id,
          err instanceof Error ? err.message : "Preview failed"
        );
      } finally {
        setFileLoading(fileEntry.id, false);
      }
    }

    // Build merged schema after all previews complete
    buildMergedSchema();
    setIsPreviewingAll(false);

    // If all files now have previews, advance to schema step
    const allHavePreviews = files.every(
      (f) =>
        f.previewData !== null ||
        validFiles.find((vf) => vf.id === f.id) !== undefined
    );
    if (allHavePreviews) {
      nextStep();
    }
  };

  // Handle batch commit
  const handleCommit = async () => {
    setIngesting(true);
    setIngestError(null);
    goToStep("ingesting");

    try {
      // Build file configs with content
      const fileConfigs = await Promise.all(
        files.map(async (f) => ({
          source: f.source,
          query_name: f.queryName,
          content: await readFileAsBase64(f.file),
          filename: f.file.name,
        }))
      );

      // Call batch commit API
      const response = await batchCommit(caseId, {
        files: fileConfigs,
        field_mappings: getMappingsArray(),
        entity_fields: entityFields,
        save_mapper: saveMapper,
        time_start: timeStart || undefined,
        time_end: timeEnd || undefined,
      });

      // Store results per file
      files.forEach((f, idx) => {
        if (response.results[idx]) {
          setResult(f.id, response.results[idx]);
        }
      });

      goToStep("complete");
    } catch (err) {
      setIngestError(err instanceof Error ? err.message : "Batch ingestion failed");
      goToStep("complete");
    } finally {
      setIngesting(false);
    }
  };

  // Get sample row for mapping display (combined from all files)
  const getSampleRow = (): Record<string, unknown> => {
    const sample: Record<string, unknown> = {};
    for (const file of files) {
      if (file.previewData?.preview_rows[0]) {
        Object.assign(sample, file.previewData.preview_rows[0]);
      }
    }
    return sample;
  };

  // Render step content
  const renderStepContent = () => {
    switch (step) {
      case "files":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-foreground mb-2">
                Upload Log Files
              </h2>
              <p className="text-sm text-muted-foreground">
                Add one or more SIEM export files to ingest. Each file needs a source
                system name and query description.
              </p>
            </div>

            <FileList
              onPreviewAll={handlePreviewAll}
              isPreviewingAll={isPreviewingAll}
            />
          </div>
        );

      case "schema":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-foreground mb-2">
                Merged Schema
              </h2>
              <p className="text-sm text-muted-foreground">
                Review the combined field schema from all files. Fields not present in
                a file will have null values for events from that file.
              </p>
            </div>

            <SchemaView />
          </div>
        );

      case "mapping":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-foreground mb-2">
                Field Mapping
              </h2>
              <p className="text-sm text-muted-foreground">
                Map source fields to the unified schema. These mappings apply to all
                files. Required fields are highlighted.
              </p>
            </div>

            <FieldMappingTable
              sourceFields={workingSchema}
              mappings={fieldMappings}
              onMappingChange={updateMapping}
              sampleRow={getSampleRow()}
              showFieldSources={files.length > 1}
            />
          </div>
        );

      case "entities":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-foreground mb-2">
                Entity Extraction
              </h2>
              <p className="text-sm text-muted-foreground">
                Choose which fields should be extracted as entities for pivoting.
              </p>
            </div>

            <EntityFieldSelector
              sourceFields={workingSchema}
              mappings={fieldMappings}
              selectedFields={entityFields}
              onToggle={toggleEntityField}
            />
          </div>
        );

      case "confirm":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-foreground mb-2">
                Confirm Batch Ingestion
              </h2>
              <p className="text-sm text-muted-foreground">
                Review your settings and start the ingestion for all{" "}
                {files.length} file{files.length !== 1 && "s"}.
              </p>
            </div>

            <IngestSummary
              saveMapper={saveMapper}
              onSaveMapperChange={setSaveMapper}
              timeStart={timeStart}
              timeEnd={timeEnd}
              onTimeStartChange={setTimeStart}
              onTimeEndChange={setTimeEnd}
            />
          </div>
        );

      case "ingesting":
      case "complete":
        return (
          <IngestProgress
            onViewTimeline={() => router.push(`/cases/${caseId}/timeline`)}
            onIngestAnother={reset}
          />
        );

      default:
        return null;
    }
  };

  // Render navigation buttons
  const renderNavigation = () => {
    if (step === "ingesting" || step === "complete") return null;

    const canGoBack = step !== "files";
    const canGoForward = canProceed();

    return (
      <div className="flex items-center justify-between pt-6 border-t border-border">
        {/* Back button */}
        {canGoBack ? (
          <button
            onClick={prevStep}
            className="flex items-center gap-2 px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
        ) : (
          <div />
        )}

        {/* Next / Submit button */}
        {step === "files" ? (
          <button
            onClick={() => {
              // If all files have previews, just go to next step
              // Otherwise, preview first
              const allHavePreviews = files.every((f) => f.previewData !== null);
              if (allHavePreviews) {
                buildMergedSchema();
                nextStep();
              } else {
                handlePreviewAll();
              }
            }}
            disabled={!canGoForward || isPreviewingAll}
            className={cn(
              "flex items-center gap-2 px-6 py-2 rounded-lg font-semibold transition-all",
              canGoForward && !isPreviewingAll
                ? "bg-cyan hover:bg-cyan/90 text-background"
                : "bg-secondary text-muted-foreground cursor-not-allowed"
            )}
          >
            {isPreviewingAll ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                Continue
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        ) : step === "confirm" ? (
          <button
            onClick={handleCommit}
            disabled={!canGoForward || isIngesting}
            className={cn(
              "flex items-center gap-2 px-6 py-2 rounded-lg font-semibold transition-all",
              canGoForward && !isIngesting
                ? "bg-cyan hover:bg-cyan/90 text-background"
                : "bg-secondary text-muted-foreground cursor-not-allowed"
            )}
          >
            {isIngesting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Ingesting...
              </>
            ) : (
              <>
                Start Batch Ingestion
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        ) : (
          <button
            onClick={nextStep}
            disabled={!canGoForward}
            className={cn(
              "flex items-center gap-2 px-6 py-2 rounded-lg font-semibold transition-all",
              canGoForward
                ? "bg-cyan hover:bg-cyan/90 text-background"
                : "bg-secondary text-muted-foreground cursor-not-allowed"
            )}
          >
            Continue
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto">
      {step !== "ingesting" && step !== "complete" && (
        <WizardSteps currentStep={step} onStepClick={goToStep} />
      )}

      <div className="metric-card">
        {renderStepContent()}
        {renderNavigation()}
      </div>
    </div>
  );
}

// Helper to read file as base64
async function readFileAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      // Remove data URL prefix
      const base64 = result.split(",")[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
