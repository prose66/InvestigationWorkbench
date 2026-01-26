"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { IngestStep } from "@/stores/ingestStore";

interface WizardStepsProps {
  currentStep: IngestStep;
  onStepClick?: (step: IngestStep) => void;
}

const STEPS: { id: IngestStep; label: string }[] = [
  { id: "files", label: "Files" },
  { id: "schema", label: "Schema" },
  { id: "mapping", label: "Mapping" },
  { id: "entities", label: "Entities" },
  { id: "confirm", label: "Confirm" },
];

const STEP_ORDER: IngestStep[] = ["files", "schema", "mapping", "entities", "confirm", "ingesting", "complete"];

export function WizardSteps({ currentStep, onStepClick }: WizardStepsProps) {
  const currentIndex = STEP_ORDER.indexOf(currentStep);

  return (
    <nav aria-label="Progress" className="mb-8">
      <ol className="flex items-center justify-between">
        {STEPS.map((step, index) => {
          const stepIndex = STEP_ORDER.indexOf(step.id);
          const isComplete = stepIndex < currentIndex;
          const isCurrent = step.id === currentStep;
          const canClick = stepIndex < currentIndex && onStepClick;

          return (
            <li key={step.id} className="flex-1">
              <div
                className={cn(
                  "group flex flex-col items-center",
                  canClick && "cursor-pointer"
                )}
                onClick={() => canClick && onStepClick(step.id)}
              >
                {/* Step indicator */}
                <div className="relative flex items-center justify-center">
                  {/* Connector line (left) */}
                  {index > 0 && (
                    <div
                      className={cn(
                        "absolute right-1/2 top-1/2 -translate-y-1/2 w-full h-0.5",
                        isComplete || isCurrent ? "bg-cyan" : "bg-border"
                      )}
                      style={{ width: "calc(100% + 2rem)" }}
                    />
                  )}

                  {/* Circle */}
                  <div
                    className={cn(
                      "relative z-10 w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300",
                      isComplete && "bg-cyan border-cyan",
                      isCurrent && "border-cyan bg-cyan/10",
                      !isComplete && !isCurrent && "border-border bg-background",
                      canClick && "group-hover:border-cyan/70"
                    )}
                  >
                    {isComplete ? (
                      <Check className="w-5 h-5 text-background" />
                    ) : (
                      <span
                        className={cn(
                          "text-sm font-semibold",
                          isCurrent ? "text-cyan" : "text-muted-foreground"
                        )}
                      >
                        {index + 1}
                      </span>
                    )}
                  </div>
                </div>

                {/* Label */}
                <span
                  className={cn(
                    "mt-2 text-xs font-medium",
                    isCurrent
                      ? "text-cyan"
                      : isComplete
                      ? "text-foreground"
                      : "text-muted-foreground"
                  )}
                >
                  {step.label}
                </span>
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
