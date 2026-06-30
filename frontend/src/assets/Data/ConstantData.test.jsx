import { describe, expect, it } from "vitest";
import React from "react";
import {
  getMachineStateUI,
  machineCriticalityColor,
  menuData,
} from "./ConstantData";

describe("ConstantData sanity checks", () => {
  it("includes expected dashboard menu route", () => {
    expect(Array.isArray(menuData)).toBe(true);

    const allItems = menuData.flatMap((section) => section.items ?? []);
    const dashboardItem = allItems.find((item) => item.path === "/");

    expect(dashboardItem).toBeDefined();
    expect(dashboardItem?.label).toBe("Dashboard");
  });

  it("keeps high criticality color configured", () => {
    expect(machineCriticalityColor.high).toBe("#734961");
  });

  it("returns a valid React element for a known machine state", () => {
    const node = getMachineStateUI("OFF");
    expect(React.isValidElement(node)).toBe(true);
  });

  it("returns null for unknown machine state", () => {
    expect(getMachineStateUI("UNKNOWN_STATE")).toBeNull();
  });
});
