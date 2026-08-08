"use client";

import { forwardRef, useId } from "react";
import { cn } from "./utils";

interface RadioOption {
  label: string;
  value: string;
}

interface RadioGroupProps {
  name?: string;
  options: RadioOption[];
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  label?: string;
  error?: string;
  disabled?: boolean;
  orientation?: "horizontal" | "vertical";
  className?: string;
}

export const RadioGroup = forwardRef<HTMLDivElement, RadioGroupProps>(
  (
    {
      name,
      options,
      value,
      defaultValue,
      onChange,
      label,
      error,
      disabled,
      orientation = "vertical",
      className,
    },
    ref
  ) => {
    const generatedName = useId();
    const groupName = name || generatedName;
    const errorId = `${groupName}-error`;
    const isControlled = value !== undefined;

    return (
      <div ref={ref} className={cn("flex flex-col", className)}>
        {label && (
          <span
            id={`${groupName}-label`}
            className="mb-2 text-sm font-medium text-[var(--text-secondary)]"
          >
            {label}
          </span>
        )}
        <div
          role="radiogroup"
          aria-labelledby={label ? `${groupName}-label` : undefined}
          aria-describedby={error ? errorId : undefined}
          aria-invalid={error ? true : undefined}
          className={cn("flex", orientation === "horizontal" ? "flex-row gap-4" : "flex-col gap-2")}
        >
          {options.map((option) => {
            const optionId = `${groupName}-${option.value}`;
            const isChecked = isControlled ? value === option.value : defaultValue === option.value;

            return (
              <label
                key={option.value}
                htmlFor={optionId}
                className={cn(
                  "inline-flex items-center gap-2 cursor-pointer select-none",
                  disabled && "cursor-not-allowed opacity-50"
                )}
              >
                <span className="relative flex items-center justify-center">
                  <input
                    type="radio"
                    id={optionId}
                    name={groupName}
                    value={option.value}
                    checked={isChecked}
                    disabled={disabled}
                    role="radio"
                    aria-checked={isChecked}
                    onChange={(e) => {
                      if (e.target.checked) {
                        onChange?.(option.value);
                      }
                    }}
                    className={cn(
                      "peer h-4 w-4 appearance-none rounded-full border transition-colors",
                      "focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)] focus:ring-offset-2",
                      error
                        ? "border-danger-500 focus:border-danger-500 focus:ring-danger-500"
                        : "border-[var(--border-default)]",
                      "checked:border-[var(--muhide-orange)]",
                      disabled && "cursor-not-allowed"
                    )}
                  />
                  {isChecked && (
                    <span
                      className={cn(
                        "pointer-events-none absolute h-2 w-2 rounded-full",
                        error ? "bg-danger-500" : "bg-[var(--muhide-orange)]"
                      )}
                      aria-hidden="true"
                    />
                  )}
                </span>
                <span className="text-sm text-[var(--text-primary)]">{option.label}</span>
              </label>
            );
          })}
        </div>
        {error && (
          <p id={errorId} role="alert" className="mt-1 text-sm text-danger-600">
            {error}
          </p>
        )}
      </div>
    );
  }
);
RadioGroup.displayName = "RadioGroup";
