export const PRODUCTION_RUN_STATUS = {
  RUNNING: "RUNNING",
  COMPLETED: "COMPLETED",
};

export function isProductionRunEditable(run) {
  return run?.status === PRODUCTION_RUN_STATUS.RUNNING;
}
