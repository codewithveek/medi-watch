import React from "react";

/**
 * Perpetual disclaimer banner displayed at all times.
 * Reminds staff that MediWatch is AI-assisted and not diagnostic.
 */
const DisclaimerBanner: React.FC = () => {
  return (
    <div
      role="alert"
      className="flex items-center gap-3 rounded-lg border border-yellow-600/30 bg-yellow-900/30 px-4 py-2.5 text-sm text-yellow-200"
    >
      <svg
        className="h-5 w-5 flex-shrink-0 text-yellow-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <span>
        <strong className="font-semibold text-yellow-100">
          AI-Assisted Monitoring
        </strong>
        {
          " — Not Diagnostic. All alerts require human verification by qualified medical staff."
        }
      </span>
    </div>
  );
};

export default DisclaimerBanner;
