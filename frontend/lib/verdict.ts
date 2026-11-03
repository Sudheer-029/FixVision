export const HEADLINE = {
  PASSED: "Passed these checks under these conditions",
  FAILED: "Failed",
  INCONCLUSIVE: "Inconclusive: not enough evidence to decide",
};

export const RESULT_LABEL: Record<string, string> = {
  pass: "Pass",
  fail: "Fail",
  insufficient_evidence: "Not enough evidence",
};

export const SUPPLY_LABEL: Record<string, string> = {
  battery_9v: "9 V battery",
  usb_5v: "5 V USB",
};

/** Reasons start with the check id (C2_flow: ...); people only need the sentence. */
export const cleanReason = (reason: string) => reason.replace(/^C\d_\w+: /, "");
