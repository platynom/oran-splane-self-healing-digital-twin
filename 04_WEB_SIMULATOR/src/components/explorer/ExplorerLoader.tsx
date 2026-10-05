"use client";
import { Suspense } from "react";
import { ExplorerPage } from "./ExplorerPage";

export function ExplorerLoader() {
  return (
    <Suspense fallback={<p role="status" className="text-muted">Loading explorer…</p>}>
      <ExplorerPage />
    </Suspense>
  );
}
