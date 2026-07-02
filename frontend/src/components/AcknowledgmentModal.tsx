"use client";

import { useEffect, useState } from "react";
import { Modal } from "@/components/Modal";
import { PrimaryButton } from "@/components/PrimaryButton";
import { authApi } from "@/lib/api";
import type { Agreement } from "@/lib/types";

interface AcknowledgmentModalProps {
  open: boolean;
  onClose: () => void;
  /** Called when the user presses "Agree & Continue"; passes the version seen. */
  onAgree: (version: string) => void;
}

/**
 * The mandatory signup agreement modal. Loads the combined Acknowledgment +
 * Terms + Privacy content and only lets the user accept after it is shown.
 */
export function AcknowledgmentModal({ open, onClose, onAgree }: AcknowledgmentModalProps) {
  const [agreement, setAgreement] = useState<Agreement | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open && !agreement) {
      authApi
        .getAgreement()
        .then(setAgreement)
        .catch(() => setError("Could not load the agreement. Please try again."));
    }
  }, [open, agreement]);

  return (
    <Modal
      open={open}
      title="Mini SoulSpace User Acknowledgment"
      onClose={onClose}
      footer={
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-full px-5 py-2 text-soul-muted hover:text-soul-accent"
          >
            Cancel
          </button>
          <PrimaryButton
            onClick={() => agreement && onAgree(agreement.version)}
          >
            Agree &amp; Continue
          </PrimaryButton>
        </div>
      }
    >
      {error && <p className="text-red-400">{error}</p>}
      {!error && !agreement && <p>Loading…</p>}
      {agreement && (
        <div className="whitespace-pre-wrap text-sm leading-relaxed">
          {agreement.content}
        </div>
      )}
    </Modal>
  );
}
